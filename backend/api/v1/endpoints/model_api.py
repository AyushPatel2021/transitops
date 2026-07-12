import logging
import base64
import io
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Request
from fastapi.responses import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.core.registry import registry
from backend.core.policy import policy_engine
from backend.core.exceptions import UserError, ValidationError, AccessError, AuthenticationError
from backend.core.middleware.permission_middleware import (
    permission_validator, 
    create_user_context_from_jwt,
    validate_domain_filter_access,
    require_permission,
    require_role
)
from backend.models.user import User
from backend.core.base_model import Environment

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from backend.services.auth_service import SECRET_KEY, ALGORITHM, get_current_user_from_jwt, validate_jwt_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

from datetime import datetime, date

# _parse_client_data is now moved to BaseModel._parse_values, so we can remove it.

logger = logging.getLogger(__name__)

async def get_current_user(current_user: User = Depends(get_current_user_from_jwt)):
    """Get current authenticated user from enhanced JWT token"""
    logger.debug(f"User authenticated: {current_user.email}, role: {current_user.role.name if current_user.role else 'None'}")
    return current_user
    return user

from backend.core.menu_manager import menu_manager

router = APIRouter()

@router.get("/ui/menu")
def get_ui_menu(current_user = Depends(get_current_user)):
    return menu_manager.get_menu(user_role=current_user.role.name if current_user.role else None)


def _resolve_current_user_defaults(metadata: dict, current_user):
    fields_meta = metadata.get("fields", metadata)
    for field_meta in fields_meta.values():
        if isinstance(field_meta, dict) and field_meta.get("default") == "current_user":
            field_meta["default"] = current_user.id
    return metadata


def _get_record_display_name(record, model_cls, fallback):
    name_field = getattr(model_cls, "_name_field_", "name")
    return getattr(record, name_field, None) or str(fallback)


@router.get("/{model_name}/permissions")
def get_model_permissions(
    model_name: str, 
    current_user = Depends(get_current_user)
):
    """Get user's permissions for a specific model"""
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    perms = {
        "create": policy_engine.can_access_record(current_user, model_name, "create", context=None),
        "read": policy_engine.can_access_record(current_user, model_name, "read", context=None),
        "write": policy_engine.can_access_record(current_user, model_name, "write", context=None),
        "delete": policy_engine.can_access_record(current_user, model_name, "delete", context=None)
    }
    logger.debug(f"get_model_permissions for {model_name}: {perms}")
    return perms

@router.get("/{model_name}/{id}/permissions")
def get_record_permissions(
    model_name: str, 
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get user's permissions for a specific record"""
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    record = model_cls.browse(id, db=db, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    perms = {
        "create": policy_engine.can_access_record(current_user, model_name, "create", record, context=None),
        "read": policy_engine.can_access_record(current_user, model_name, "read", record, context=None),
        "write": policy_engine.can_access_record(current_user, model_name, "write", record, context=None),
        "delete": policy_engine.can_access_record(current_user, model_name, "delete", record, context=None)
    }
    logger.debug(f"get_record_permissions for {model_name}/{id}: {perms}")
    return perms

@router.get("/meta/{model_name}")
def get_model_metadata(model_name: str, current_user = Depends(get_current_user)):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise ValidationError(f"Model '{model_name}' not found")
    
    # Use policy_engine to filter metadata based on role
    result = policy_engine.get_visible_fields(current_user, model_cls)
    return _resolve_current_user_defaults(result, current_user)

@router.get("/meta/{model_name}/enhanced")
def get_enhanced_metadata(model_name: str, current_user = Depends(get_current_user)):
    """
    Get enhanced metadata with domain expression validation and field information.
    """
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise ValidationError(f"Model '{model_name}' not found")
    
    logger.debug(f"Getting enhanced metadata for {model_name} (User: {current_user.email})")
    
    # Get enhanced metadata with validation
    enhanced_metadata = model_cls.get_ui_metadata(user_role=current_user.role.name)
    domain_fields = model_cls.get_domain_fields()
    _resolve_current_user_defaults(enhanced_metadata, current_user)
    
    # Get search configuration
    search_config = getattr(model_cls, '_search_config', {})
    
    logger.debug(f"Domain fields found for {model_name}: {domain_fields}")
    
    return {
        "metadata": enhanced_metadata,
        "domain_fields": domain_fields,
        "search_config": search_config,
        "model_name": model_name
    }

@router.post("/meta/{model_name}/evaluate")
def evaluate_metadata_context(
    model_name: str, 
    request: Request,
    context: dict, 
    current_user = Depends(get_current_user)
):
    """
    Evaluate metadata with context using secure JWT-based user context.
    This replaces localStorage-based user context with server-validated JWT claims.
    """
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        # Extract JWT token from request
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="JWT token required")
        
        token = auth_header.split(' ')[1]
        jwt_claims = validate_jwt_token(token)
        
        # Validate permission to access metadata
        if not permission_validator.validate_model_permission(jwt_claims, model_name, 'read'):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions for {model_name}.read")
        
        # Create secure user context from JWT claims (not localStorage)
        user_context = create_user_context_from_jwt(jwt_claims)
        
        evaluated_metadata = model_cls.get_metadata_with_context(
            context=context, 
            user_role=jwt_claims.get('role'),
            user_context=user_context
        )
        return evaluated_metadata
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error evaluating metadata: {str(e)}")

@router.get("/meta/{model_name}/domain-fields")
def get_domain_fields(model_name: str, current_user = Depends(get_current_user)):
    """
    Get list of fields that have domain expressions.
    """
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return model_cls.get_domain_fields()

@router.post("/{model_name}/default_get")
def get_model_defaults(
    model_name: str, 
    payload: dict,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get default values for a model.
    Payload: {"fields": ["field1", "field2", ...]}
    """
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
        
    fields_list = payload.get("fields", [])
    if not fields_list:
        # Default to all fields defined in metadata
        fields_list = list(model_cls._ui_metadata.keys())
        
    defaults = model_cls.default_get(fields_list)
    env = Environment(db, user_id=current_user.id)

    for field_name, value in list(defaults.items()):
        field_def = model_cls._field_definitions.get(field_name)
        if not field_def:
            continue

        if value == "current_user":
            value = current_user.id
            defaults[field_name] = value

        if field_def.field_type == "many2one" and isinstance(value, int):
            rel_cls = registry.get_model(field_def.comodel_name)
            if rel_cls:
                rec = env[field_def.comodel_name].browse(value)
                if rec:
                    raw_record = rec._records[0] if getattr(rec, "_records", None) else rec
                    defaults[field_name] = {
                        "id": value,
                        "display_name": _get_record_display_name(raw_record, rel_cls, value)
                    }

    return defaults

@router.post("/{model_name}/onchange")
def trigger_model_onchange(
    model_name: str, 
    payload: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Trigger onchange logic for a model.
    Payload: {"vals": {...}, "field_name": "field_that_changed"}
    """
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
        
    vals = payload.get("vals", {})
    field_name = payload.get("field_name")
    
    if not field_name:
        raise HTTPException(status_code=400, detail="field_name is required")
        
    try:
        return model_cls.trigger_onchange(vals, field_name, db=db)
    except Exception as e:
        logger.error(f"Error in onchange API for {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_name}")
def list_records(
    model_name: str, 
    request: Request,
    search: str = None, 
    search_field: str = None, 
    domain: str = None,
    filters: str = None,  # New parameter for filter names
    groupBy: str = None,
    limit: int = 80, 
    offset: int = 0,
    parent_model: str = None,  # New parameter to indicate this is a many2one relation request
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    import time
    start_time = time.time()
    
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        # Extract JWT token and validate permissions
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="JWT token required")
        
        token = auth_header.split(' ')[1]
        jwt_claims = validate_jwt_token(token)
        
        # Validate permission to read records
        if not permission_validator.validate_model_permission(jwt_claims, model_name, 'read'):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions for {model_name}.read")
        
        # Validate domain-based filtering if filters are provided
        if filters:
            import json
            try:
                filter_dict = json.loads(filters) if isinstance(filters, str) else filters
                if not validate_domain_filter_access(jwt_claims, filter_dict):
                    raise HTTPException(status_code=403, detail="Domain filter access denied")
            except json.JSONDecodeError:
                pass  # Continue with original filter validation
        
        # Check permissions with context for many2one relations
        context = None
        if parent_model:
            context = {
                'is_many2one_relation': True,
                'parent_model': parent_model
            }
        
        if not policy_engine.can_access_record(current_user, model_name, "read", context=context):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        from sqlalchemy.orm import joinedload
        
        env = Environment(db, user_id=current_user.id)
        # Build query with eager loading for many2one relationships
        query = db.query(model_cls)
        
        # Apply role-based domain filtering FIRST
        query = policy_engine.apply_domain_filter(query, current_user, model_name)
        
        # Add eager loading for many2one relationships to prevent N+1 queries
        many2one_fields = []
        for field_name, field_meta in model_cls._ui_metadata.items():
            if field_meta.get("type") == "many2one":
                rel_attr = field_meta.get("relation_attr")
                if rel_attr:
                    relation_attr = getattr(model_cls, rel_attr, None)
                    if relation_attr is not None:
                        try:
                            query = query.options(joinedload(relation_attr))
                            many2one_fields.append(field_name)
                        except Exception as e:
                            logger.debug(f"Could not eager load {field_name}: {e}")
        
        # Apply additional domain filter (JSON list of triplets or Polish notation)
        if domain:
            logger.debug(f"LIST records domain={domain}")
            import json
            from datetime import datetime, date, timedelta
            try:
                # Define evaluation context with user recordset
                eval_context = {
                    "user": env.user,
                    "datetime": datetime,
                    "timedelta": timedelta,
                    "date": date,
                    "True": True,
                    "False": False,
                    "None": None
                }
                
                # Check if it looks like a dynamic expression or JSON
                try:
                    # literal_eval/eval to support dynamic components like user.id
                    domain_list = eval(domain, {"__builtins__": {}}, eval_context)
                except Exception:
                    # Fallback to pure JSON if eval fails
                    domain_list = json.loads(domain)
                
                if isinstance(domain_list, list):
                    query = model_cls.apply_domain_to_query(query, domain_list)
            except Exception as e:
                logger.debug(f"Domain parsing error: {e}")

        # Apply predefined filters
        if filters:
            import json
            from datetime import datetime, timedelta, date
            
            try:
                filter_names = json.loads(filters) if isinstance(filters, str) else filters
                if isinstance(filter_names, list):
                    search_config = getattr(model_cls, '_search_config', {})
                    available_filters = search_config.get('filters', [])
                    
                    # Define safe evaluation context for dynamic domains
                    eval_context = {
                        "user": env.user,
                        "datetime": datetime,
                        "timedelta": timedelta,
                        "date": date,
                        "True": True,
                        "False": False,
                        "None": None
                    }

                    for filter_name in filter_names:
                        # Find the filter definition in _search_config
                        filter_def = next((f for f in available_filters if f['name'] == filter_name), None)
                        
                        if filter_def and filter_def.get('domain'):
                            domain_str = filter_def['domain']
                            try:
                                # Dynamic evaluation of the domain string
                                # matches functionality of Znova's safe_eval but using python's eval with restricted globals
                                # This allows strings like "[('warranty_expiry', '<', datetime.now())]" to be evaluated
                                domain_list = eval(domain_str, {"__builtins__": {}}, eval_context)
                                
                                if isinstance(domain_list, list):
                                    query = model_cls.apply_domain_to_query(query, domain_list)
                                
                                logger.debug(f"Applied dynamic filter '{filter_name}': {domain_str}")
                            except Exception as e:
                                logger.error(f"Error evaluating dynamic domain for {filter_name}: {e}")
            except Exception as e:
                logger.error(f"Filter parsing error: {e}")

        # Apply search filter
        if search and search_field:
            meta = model_cls._ui_metadata.get(search_field)
            if meta:
                if meta.get("type") == "many2one":
                    rel_attr_name = meta.get("relation_attr")
                    if rel_attr_name and hasattr(model_cls, rel_attr_name):
                        rel_attr = getattr(model_cls, rel_attr_name)
                        rel_model = rel_attr.property.mapper.class_
                        
                        # Find a name-like field in the related model
                        name_field = next((c.name for c in rel_model.__table__.columns if c.name in ['name', 'full_name', 'subject', 'email']), 'id')
                        
                        query = query.join(rel_attr).filter(getattr(rel_model, name_field).ilike(f"%{search}%"))
                else:
                    # Normal field search
                    if hasattr(model_cls, search_field):
                        query = query.filter(getattr(model_cls, search_field).ilike(f"%{search}%"))

        # Handle groupBy parameter
        grouped_results = None
        if groupBy:
            # Check if groupBy is a named group in search config
            search_config = getattr(model_cls, '_search_config', {})
            group_conf = next((g for g in search_config.get('group_by', []) if g['name'] == groupBy), None)
            
            # Use the field from config if found, otherwise assume groupBy is the field name
            group_field = group_conf['field'] if group_conf else groupBy
            
            if hasattr(model_cls, group_field):
                from sqlalchemy import func
                
                group_attr = getattr(model_cls, group_field)
                meta = model_cls._ui_metadata.get(group_field, {})
            
            if meta.get("type") == "many2one":
                # For many2one fields, group by the related record's display name
                rel_attr_name = meta.get("relation_attr")
                if rel_attr_name and hasattr(model_cls, rel_attr_name):
                    # Get the relationship attribute (e.g., Equipment.category)
                    rel_attr = getattr(model_cls, rel_attr_name)
                    rel_model = rel_attr.property.mapper.class_
                    name_field = next((c.name for c in rel_model.__table__.columns if c.name in ['name', 'full_name', 'subject', 'email']), 'id')
                    
                    # Group by both the foreign key ID and display name for proper grouping
                    # Use the foreign key field (group_attr) for grouping, but join via relationship (rel_attr)
                    group_query = query.join(rel_attr).with_entities(
                        group_attr.label('group_id'),  # Foreign key value (e.g., category_id)
                        getattr(rel_model, name_field).label('group_name'),  # Display name (e.g., category.name)
                        func.count(model_cls.id).label('count')
                    ).group_by(group_attr, getattr(rel_model, name_field))
                    
                    # Now fetch the actual records for each group
                    groups_with_records = []
                    for row in group_query.all():
                        # Get records for this group using the foreign key value
                        # Create a fresh query to avoid any join issues
                        fresh_query = db.query(model_cls)
                        fresh_query = policy_engine.apply_domain_filter(fresh_query, current_user, model_name)
                        
                        # Apply the same domain filter as the main query
                        if domain:
                            import json
                            from datetime import datetime, date, timedelta
                            try:
                                eval_context = {
                                    "user": env.user,
                                    "datetime": datetime,
                                    "timedelta": timedelta,
                                    "date": date,
                                    "True": True,
                                    "False": False,
                                    "None": None
                                }
                                try:
                                    domain_list = eval(domain, {"__builtins__": {}}, eval_context)
                                except Exception:
                                    domain_list = json.loads(domain)
                                
                                if isinstance(domain_list, list):
                                    fresh_query = model_cls.apply_domain_to_query(fresh_query, domain_list)
                            except Exception as e:
                                logger.debug(f"Domain parsing error in groupBy: {e}")
                        
                        # Apply predefined filters to grouped query
                        if filters:
                            import json
                            from datetime import datetime, timedelta, date
                            try:
                                filter_names = json.loads(filters) if isinstance(filters, str) else filters
                                if isinstance(filter_names, list):
                                    search_config = getattr(model_cls, '_search_config', {})
                                    available_filters = search_config.get('filters', [])
                                    
                                    eval_context = {
                                        "user": env.user,
                                        "datetime": datetime,
                                        "timedelta": timedelta,
                                        "date": date,
                                        "True": True,
                                        "False": False,
                                        "None": None
                                    }

                                    for filter_name in filter_names:
                                        filter_def = next((f for f in available_filters if f['name'] == filter_name), None)
                                        if filter_def and filter_def.get('domain'):
                                            domain_str = filter_def['domain']
                                            try:
                                                domain_list = eval(domain_str, {"__builtins__": {}}, eval_context)
                                                if isinstance(domain_list, list):
                                                    fresh_query = model_cls.apply_domain_to_query(fresh_query, domain_list)
                                            except Exception as e:
                                                logger.error(f"Error evaluating filter in groupBy: {e}")
                            except Exception as e:
                                logger.error(f"Filter parsing error in groupBy: {e}")
                        
                        # Apply search filter to grouped query
                        if search and search_field:
                            search_meta = model_cls._ui_metadata.get(search_field)
                            if search_meta:
                                if search_meta.get("type") == "many2one":
                                    search_rel_attr_name = search_meta.get("relation_attr")
                                    if search_rel_attr_name and hasattr(model_cls, search_rel_attr_name):
                                        search_rel_attr = getattr(model_cls, search_rel_attr_name)
                                        search_rel_model = search_rel_attr.property.mapper.class_
                                        search_name_field = next((c.name for c in search_rel_model.__table__.columns if c.name in ['name', 'full_name', 'subject', 'email']), 'id')
                                        fresh_query = fresh_query.join(search_rel_attr).filter(getattr(search_rel_model, search_name_field).ilike(f"%{search}%"))
                                else:
                                    if hasattr(model_cls, search_field):
                                        fresh_query = fresh_query.filter(getattr(model_cls, search_field).ilike(f"%{search}%"))
                        
                        # Filter by the group value using the foreign key
                        group_records = fresh_query.filter(group_attr == row.group_id).all()
                        
                        groups_with_records.append({
                            'value': row.group_name,  # Normalized to 'value' for frontend
                            'group_id': row.group_id,
                            'count': row.count,
                            'items': [r.to_dict(user_role=current_user.role.name) for r in group_records]
                        })
                    
                    grouped_results = groups_with_records
            elif meta.get("type") == "selection":
                # For selection fields, group by the selection value
                group_query = query.with_entities(
                    group_attr.label('group_value'),
                    func.count(model_cls.id).label('count')
                ).group_by(group_attr)
                
                options = meta.get("options", {})
                groups_with_records = []
                
                for row in group_query.all():
                    # Get records for this group
                    group_records_query = query.filter(group_attr == row.group_value)
                    group_records = group_records_query.all()
                    
                    display_name = (options.get(row.group_value, {}).get('label') if isinstance(options.get(row.group_value), dict) 
                                   else options.get(row.group_value, row.group_value)) or str(row.group_value)
                    
                    groups_with_records.append({
                        'value': display_name,  # Normalized to 'value' for frontend
                        'group_value': row.group_value,
                        'count': row.count,
                        'items': [r.to_dict(user_role=current_user.role.name) for r in group_records]
                    })
                
                grouped_results = groups_with_records
            else:
                # For other field types, group by the field value directly
                group_query = query.with_entities(
                    group_attr.label('group_value'),
                    func.count(model_cls.id).label('count')
                ).group_by(group_attr)
                
                groups_with_records = []
                
                for row in group_query.all():
                    # Get records for this group
                    group_records_query = query.filter(group_attr == row.group_value)
                    group_records = group_records_query.all()
                    
                    groups_with_records.append({
                        'value': str(row.group_value) if row.group_value is not None else 'None',  # Normalized to 'value'
                        'group_value': row.group_value,
                        'count': row.count,
                        'items': [r.to_dict(user_role=current_user.role.name) for r in group_records]
                    })
                
                grouped_results = groups_with_records

        # Get total count before applying limit/offset
        count_start = time.time()
        total = query.count()
        count_time = time.time() - count_start
        
        # Apply pagination
        fetch_start = time.time()
        records = query.offset(offset).limit(limit).all()
        fetch_time = time.time() - fetch_start
        
        # Convert to dict - optimize by only serializing necessary fields and limiting depth
        dict_start = time.time()
        # For list views, we typically only need the fields defined in the list view metadata
        list_fields = model_cls._ui_views.get('list', {}).get('fields', [])
        target_fields = list_fields if list_fields else None
        
        items = [r.to_dict(fields=target_fields, user_role=current_user.role.name, max_depth=1) for r in records]
        dict_time = time.time() - dict_start
        
        total_time = time.time() - start_time
        
        # Only log slow queries (>500ms)
        if total_time > 0.5:
            logger.warning(
                f"Slow query - Model List {model_name}: {len(records)} records in {total_time:.3f}s "
                f"(count: {count_time:.3f}s, fetch: {fetch_time:.3f}s, dict: {dict_time:.3f}s)"
            )
        
        return {
            "items": items,
            "total": total,
            "grouped_results": grouped_results if groupBy else None,
            "group_by": groupBy
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing {model_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_name}/{id}")
def get_record(
    model_name: str, 
    id: int, 
    request: Request,
    include_domain_states: bool = False,
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    try:
        # Extract JWT token and validate permissions
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="JWT token required")
        
        token = auth_header.split(' ')[1]
        jwt_claims = validate_jwt_token(token)
        
        # Validate permission to read record
        if not permission_validator.validate_model_permission(jwt_claims, model_name, 'read'):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions for {model_name}.read")
        
        # Check basic read permission
        if not policy_engine.can_access_record(current_user, model_name, "read", context=None):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        env = Environment(db, user_id=current_user.id)
        # Get record with domain filtering applied
        record = env[model_name].browse(id)
        
        if not record:
            raise HTTPException(status_code=404, detail="Record not found or access denied")
        
        # Validate domain-based access to this specific record
        record_data = {}
        if not permission_validator.validate_domain_based_access(jwt_claims, record_data):
            raise HTTPException(status_code=403, detail="Domain access denied")
        
        # Create secure user context from JWT claims (not localStorage)
        user_context = create_user_context_from_jwt(jwt_claims)
            
        return record.to_dict(
            user_role=jwt_claims.get('role'), 
            include_domain_states=include_domain_states,
            user_context=user_context
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving record: {str(e)}")

@router.post("/{model_name}")
def create_record(model_name: str, request: Request, data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
        
    logger.debug(f"create_record: model={model_name}, user={current_user.email}")
    
    try:
        # Extract JWT token and validate permissions
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="JWT token required")
        
        token = auth_header.split(' ')[1]
        jwt_claims = validate_jwt_token(token)
        
        # Validate permission to create record
        if not permission_validator.validate_model_permission(jwt_claims, model_name, 'create'):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions for {model_name}.create")
        
        # Validate domain-based access for the data being created
        if not permission_validator.validate_domain_based_access(jwt_claims, data):
            raise HTTPException(status_code=403, detail="Domain access denied for create operation")
        
        if not policy_engine.can_access_record(current_user, model_name, "create", context=None):
            logger.warning(f"Access DENIED for create on {model_name} (User: {current_user.email})")
            raise HTTPException(status_code=403, detail="Permission denied")
        logger.debug(f"Access GRANTED for create on {model_name}")
            
        # Create secure user context from JWT claims (not localStorage)
        user_context = create_user_context_from_jwt(jwt_claims)
        
        env = Environment(db, user_id=current_user.id)
        # Use simple model_cls.create() which does the duplicate check and raises UserError
        record = env[model_name].create(data)
        return record.to_dict(user_role=jwt_claims.get('role'), include_domain_states=True, user_context=user_context)
    except UserError as e:
         # 400 Bad Request is appropriate for user errors (validation)
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ERROR creating {model_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{model_name}/{id}")
def update_record(model_name: str, id: int, request: Request, data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
        
    record = model_cls.browse(id, db=db, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    logger.debug(f"update_record: model={model_name}, id={id}, user={current_user.email}")
    
    try:
        # Extract JWT token and validate permissions
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="JWT token required")
        
        token = auth_header.split(' ')[1]
        jwt_claims = validate_jwt_token(token)
        
        # Validate permission to update record
        if not permission_validator.validate_model_permission(jwt_claims, model_name, 'write'):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions for {model_name}.write")
        
        # Validate domain-based access to the existing record
        record_data = {}
        if not permission_validator.validate_domain_based_access(jwt_claims, record_data):
            raise HTTPException(status_code=403, detail="Domain access denied for existing record")
        
        # Validate domain-based access for the updated data
        if not permission_validator.validate_domain_based_access(jwt_claims, data):
            raise HTTPException(status_code=403, detail="Domain access denied for update data")
        
        if not policy_engine.can_access_record(current_user, model_name, "write", record, context=None):
            logger.warning(f"Access DENIED for write on {model_name}/{id} (User: {current_user.email})")
            raise HTTPException(status_code=403, detail="Permission denied")
        logger.debug(f"Access GRANTED for write on {model_name}/{id}")
            
        # Create secure user context from JWT claims (not localStorage)
        user_context = create_user_context_from_jwt(jwt_claims)
        
        # Use record.write() which checks for duplicates too
        record.write(data)
        return record.to_dict(user_role=jwt_claims.get('role'), include_domain_states=True, user_context=user_context)
    except UserError as e:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        # Log error and re-raise with proper error handling
        logger.error(f"ERROR updating {model_name} {id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{model_name}/{id}/audit-logs")
def get_audit_logs(
    model_name: str,
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get audit log entries for a specific record.
    Returns the history of field changes for the record.
    """
    try:
        from backend.models.audit_log import AuditLog
        from backend.models.user import User
        from sqlalchemy.orm import joinedload
        
        # Query audit logs for this record, eagerly load user relationship
        logs = db.query(AuditLog).options(
            joinedload(AuditLog.user)  # Eagerly load the user relationship
        ).filter(
            AuditLog.res_model == model_name,
            AuditLog.res_id == id
        ).order_by(AuditLog.changed_at.desc()).all()
        
        # Convert to dict format
        result = []
        for log in logs:
            # Get user info from the relationship
            user_info = None
            if hasattr(log, 'user') and log.user:
                user = log.user
                user_info = {
                    'id': user.id,
                    'name': user.full_name if hasattr(user, 'full_name') else user.email,
                    'email': user.email,
                    'image': user.image if hasattr(user, 'image') else None
                }
            
            result.append({
                'id': log.id,
                'field_name': log.field_name,
                'field_label': log.field_label,
                'old_value': log.old_value,
                'new_value': log.new_value,
                'change_type': log.change_type,
                'changed_at': log.changed_at.isoformat() if log.changed_at else None,
                'user': user_info,
                'changes_json': log.changes_json if hasattr(log, 'changes_json') else None
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching audit logs for {model_name}:{id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_name}/{id}")
def delete_record(
    model_name: str, 
    id: int, 
    request: Request,
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
        
    record = model_cls.browse(id, db=db, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    try:
        # Extract JWT token and validate permissions
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="JWT token required")
        
        token = auth_header.split(' ')[1]
        jwt_claims = validate_jwt_token(token)
        
        # Validate permission to delete record
        if not permission_validator.validate_model_permission(jwt_claims, model_name, 'delete'):
            raise HTTPException(status_code=403, detail=f"Insufficient permissions for {model_name}.delete")
        
        # Validate domain-based access to the record
        record_data = {}
        if not permission_validator.validate_domain_based_access(jwt_claims, record_data):
            raise HTTPException(status_code=403, detail="Domain access denied")
        
        if not policy_engine.can_access_record(current_user, model_name, "delete", record, context=None):
            raise HTTPException(status_code=403, detail="Permission denied")
            
        env = Environment(db, user_id=current_user.id)
        record = env[model_name].browse(id)
        if not record:
             raise HTTPException(status_code=404, detail="Record not found")
             
        record.unlink()
        return {"status": "success"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{model_name}/bulk_delete")
def bulk_delete_records(
    model_name: str, 
    payload: dict, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    ids = payload.get("ids", [])
    if not ids:
        return {"status": "success", "count": 0}
        
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
        
    env = Environment(db, user_id=current_user.id)
    records = env[model_name].browse(ids)
    
    deleted_count = 0
    for record in records:
        if policy_engine.can_access_record(current_user, model_name, "delete", record, context=None):
            record.unlink()
            deleted_count += 1
            
    return {"status": "success", "count": deleted_count}

@router.post("/{model_name}/{id}/call/{method_name}")
def call_model_method(
    model_name: str, 
    id: int, 
    method_name: str, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
        
    env = Environment(db, user_id=current_user.id)
    record = env[model_name].browse(id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
        
    if not policy_engine.can_access_record(current_user, model_name, "read", record, context=None):
        raise HTTPException(status_code=403, detail="Permission denied")

    if method_name.startswith("action_") and not method_name.startswith("action_view"):
        if not policy_engine.can_access_record(current_user, model_name, "write", record, context=None):
            raise HTTPException(status_code=403, detail="Permission denied")
        
    method = getattr(record, method_name, None)
    if not method or not callable(method):
        raise HTTPException(status_code=400, detail=f"Method '{method_name}' not found or not callable on {model_name}")

    try:
        if getattr(record, "_records", None):
            for raw_record in record._records:
                setattr(raw_record, "_action_user_id", current_user.id)
                setattr(raw_record, "_audit_user_id", current_user.id)

        # Call the method
        result = method()
        db.commit()
        if getattr(record, "_records", None):
            for raw_record in record._records:
                db.refresh(raw_record)
        return result
    except Exception as e:
        db.rollback()
        # Let the exception bubble up to FastAPI exception handlers
        # Don't convert to HTTPException here - let UserError, ValidationError, etc. be handled properly
        raise e


@router.get("/{model_name}/{id}/comparison")
def get_record_comparison(
    model_name: str,
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")

    env = Environment(db, user_id=current_user.id)
    record = env[model_name].browse(id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if not policy_engine.can_access_record(current_user, model_name, "read", record, context=None):
        raise HTTPException(status_code=403, detail="Permission denied")

    method = getattr(record, "get_comparison_payload", None)
    if not method or not callable(method):
        raise HTTPException(status_code=400, detail=f"Comparison is not supported for {model_name}")

    try:
        return method()
    except Exception as e:
        db.rollback()
        raise e


@router.get("/{model_name}/{id}/report_pdf")
def download_record_pdf_report(
    model_name: str,
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")

    env = Environment(db, user_id=current_user.id)
    record = env[model_name].browse(id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    if not policy_engine.can_access_record(current_user, model_name, "read", record, context=None):
        raise HTTPException(status_code=403, detail="Permission denied")

    method = getattr(record, "generate_report_pdf", None)
    if not method or not callable(method):
        raise HTTPException(status_code=400, detail=f"PDF report is not supported for {model_name}")

    try:
        pdf_bytes = method()
        raw_record = record._records[0] if getattr(record, "_records", None) else record
        filename = f"{getattr(raw_record, 'name', f'{model_name}-{id}')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        db.rollback()
        raise e


# ====================================
# Wizard (TransientModel) Endpoints
# ====================================

@router.post("/{model_name}/wizard")
async def create_wizard(
    model_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Create a transient wizard record and return its metadata + ID.
    """
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail=f"Wizard model '{model_name}' not found")
    
    # Verify this is actually a transient model
    if not getattr(model_cls, '_transient', False):
        raise HTTPException(status_code=400, detail=f"Model '{model_name}' is not a transient model")
    
    # Parse context from request body (contains default values like default_match_id)
    try:
        context = await request.json()
    except Exception:
        context = {}
    
    # Build initial values from context (keys prefixed with 'default_')
    initial_vals = {}
    for key, value in context.items():
        if key.startswith('default_'):
            field_name = key[8:]  # Remove 'default_' prefix
            initial_vals[field_name] = value
    
    env = Environment(db, user_id=current_user.id)
    
    try:
        # Create the wizard record
        wizard_record = env[model_name].create(initial_vals)
        db.commit()
        db.refresh(wizard_record._records[0] if hasattr(wizard_record, '_records') else wizard_record)
        
        # Get the record ID
        record_id = wizard_record.id if hasattr(wizard_record, 'id') else wizard_record._records[0].id
        
        # Get metadata for the wizard form
        metadata = model_cls.get_ui_metadata(user_role=current_user.role.name)
        
        # Serialize the wizard record
        real_record = wizard_record._records[0] if hasattr(wizard_record, '_records') else wizard_record
        record_data = real_record.to_dict(user_role=current_user.role.name)
        
        return {
            "wizard_id": record_id,
            "metadata": metadata,
            "data": record_data,
            "model_name": model_name
        }
    except Exception as e:
        db.rollback()
        raise e


@router.post("/{model_name}/{wizard_id}/wizard_execute/{method_name}")
async def execute_wizard(
    model_name: str,
    wizard_id: int,
    method_name: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Execute a wizard method (e.g., action_confirm), then auto-delete the wizard record.
    """
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail=f"Wizard model '{model_name}' not found")
    
    if not getattr(model_cls, '_transient', False):
        raise HTTPException(status_code=400, detail=f"Model '{model_name}' is not a transient model")
    
    env = Environment(db, user_id=current_user.id)
    wizard = env[model_name].browse(wizard_id)
    
    if not wizard or not wizard.exists():
        raise HTTPException(status_code=404, detail="Wizard record not found")
    
    # Update wizard with any form data from the request body
    try:
        form_data = await request.json()
        if form_data and isinstance(form_data, dict):
            # Filter out non-field keys
            update_vals = {k: v for k, v in form_data.items() if k not in ('method', 'wizard_id')}
            if update_vals:
                wizard.write(update_vals)
    except Exception:
        pass
    
    method = getattr(wizard, method_name, None)
    if not method or not callable(method):
        raise HTTPException(status_code=400, detail=f"Method '{method_name}' not found on wizard")
    
    try:
        # Execute the wizard action
        result = method()
        
        # Auto-delete the wizard record after execution
        try:
            wizard_record = wizard._records[0] if hasattr(wizard, '_records') else wizard
            db.delete(wizard_record)
        except Exception:
            pass  # Non-critical: cleanup will happen via cron
        
        db.commit()
        return result or {"type": "ir.actions.client", "tag": "close_wizard"}
    except Exception as e:
        db.rollback()
        raise e

@router.post("/{model_name}/{record_id}/upload_image/{field_name}")
async def upload_image(
    model_name: str,
    record_id: int,
    field_name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Upload an image to a specific field of a record"""
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Get the record
    record = model_cls.browse(record_id, db=db, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Check write permission
    if not policy_engine.can_access_record(current_user, model_name, "write", record, context=None):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Validate field exists and is an image field
    field_metadata = model_cls.get_field_metadata(field_name)
    if not field_metadata or field_metadata.get("type") != "image":
        raise HTTPException(status_code=400, detail=f"Field '{field_name}' is not an image field")
    
    # Get validated field configuration (includes defaults and validation)
    max_size = field_metadata.get("max_size", 5242880)  # Default 5MB
    allowed_formats = field_metadata.get("allowed_formats", ["jpeg", "jpg", "png", "gif", "webp"])
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Validate file size
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size ({len(file_content)} bytes) exceeds maximum allowed size ({max_size} bytes)"
            )
        
        # Validate file type using PIL
        try:
            image = Image.open(io.BytesIO(file_content))
            image_format = image.format.lower() if image.format else None
            
            # Check if format is allowed
            if image_format not in allowed_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image format '{image_format}' not allowed. Supported formats: {', '.join(allowed_formats)}"
                )
            
            # Verify image can be processed
            image.verify()
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
        
        # Convert to base64 for storage
        base64_data = base64.b64encode(file_content).decode('utf-8')
        image_data = f"data:image/{image_format};base64,{base64_data}"
        
        # Update the record
        setattr(record, field_name, image_data)
        db.commit()
        
        return {
            "status": "success",
            "message": "Image uploaded successfully",
            "field_name": field_name,
            "file_size": len(file_content),
            "format": image_format
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        raise HTTPException(status_code=500, detail=f"Error uploading image: {str(e)}")

@router.get("/{model_name}/{record_id}/image/{field_name}")
async def get_image(
    model_name: str,
    record_id: int,
    field_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Retrieve an image from a specific field of a record"""
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    env = Environment(db, user_id=current_user.id)
    # Get the record with domain filtering
    record = env[model_name].browse(record_id)
    
    if not record:
        raise HTTPException(status_code=404, detail="Record not found or access denied")
    
    # Check read permission
    if not policy_engine.can_access_record(current_user, model_name, "read", record, context=None):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Validate field exists and is an image field
    field_metadata = model_cls.get_field_metadata(field_name)
    if not field_metadata or field_metadata.get("type") != "image":
        raise HTTPException(status_code=400, detail=f"Field '{field_name}' is not an image field")
    
    # Get image data
    image_data = getattr(record, field_name, None)
    if not image_data:
        raise HTTPException(status_code=404, detail="No image found for this field")
    
    try:
        # Parse base64 data URL
        if image_data.startswith('data:image/'):
            # Extract format and base64 data
            header, base64_data = image_data.split(',', 1)
            content_type = header.split(';')[0].replace('data:', '')
            
            # Decode base64
            image_bytes = base64.b64decode(base64_data)
            
            return Response(
                content=image_bytes,
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=3600"}
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid image data format")
            
    except Exception as e:
        logger.error(f"Error retrieving image: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")

@router.delete("/{model_name}/{record_id}/image/{field_name}")
async def delete_image(
    model_name: str,
    record_id: int,
    field_name: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete an image from a specific field of a record"""
    model_cls = registry.get_model(model_name)
    if not model_cls:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Get the record
    record = model_cls.browse(record_id, db=db, user_id=current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Check write permission
    if not policy_engine.can_access_record(current_user, model_name, "write", record, context=None):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Validate field exists and is an image field
    field_metadata = model_cls.get_field_metadata(field_name)
    if not field_metadata or field_metadata.get("type") != "image":
        raise HTTPException(status_code=400, detail=f"Field '{field_name}' is not an image field")
    
    try:
        # Clear the image field
        setattr(record, field_name, None)
        db.commit()
        
        return {
            "status": "success",
            "message": "Image deleted successfully",
            "field_name": field_name
        }
        
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")
