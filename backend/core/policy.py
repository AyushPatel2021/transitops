from .acl import RoleName, Permission

class PolicyEngine:
    @staticmethod
    def can_access_record(user, model_name, action, record=None, context=None):
        """Check if user has permission to perform action on model/record"""
        
        if not user or not user.role:
            return False
        
        role_name = user.role.name
        
        # Admin always has full access
        if role_name == RoleName.ADMIN:
            return True
        
        # Special case: Allow read access to related models for many2one fields
        # If this is a read request for a related model and the user has read access to the parent model
        if action == 'read' and context and context.get('is_many2one_relation'):
            parent_model = context.get('parent_model')
            if parent_model and parent_model != model_name:  # Prevent infinite recursion
                if PolicyEngine.can_access_record(user, parent_model, 'read', context=None):
                    return True
            
        # Get model class to check role permissions
        from backend.core.registry import registry
        model_cls = registry.get_model(model_name)
        if not model_cls:
            return False
            
        # Check if model has role permissions defined
        if hasattr(model_cls, '_role_permissions'):
            role_perms = model_cls._role_permissions.get(role_name, {})
            result = role_perms.get(action, False)
            return result
        
        return False

    @staticmethod
    def get_domain_filter(user, model_name):
        """Get domain filter for user's role on specific model"""
        if not user or not user.role:
            return []
        
        role_name = user.role.name
        
        # Get model class to check domain rules
        from backend.core.registry import registry
        model_cls = registry.get_model(model_name)
        if not model_cls or not hasattr(model_cls, '_role_permissions'):
            return []
            
        role_perms = model_cls._role_permissions.get(role_name, {})
        domain = role_perms.get('domain', [])
        
        # Replace user context variables in domain
        return PolicyEngine._resolve_domain_context(domain, user)
    
    @staticmethod
    def _resolve_domain_context(domain, user):
        """Replace user context variables in domain rules"""
        import logging
        logger = logging.getLogger(__name__)
        
        resolved_domain = []
        
        logger.debug(f"Resolving domain context. Original domain: {domain}, User: {user}")
        
        for criterion in domain:
            if (isinstance(criterion, tuple) or isinstance(criterion, list)) and len(criterion) == 3:
                field, operator, value = criterion
                
                # Replace user context variables (e.g., "user.id", "user.partner_id.id")
                if isinstance(value, str) and value.startswith('user.'):
                    parts = value.split('.')
                    resolved_value = user
                    
                    try:
                        for part in parts[1:]:
                            if resolved_value is not None:
                                # If it's a Recordset/Model, use getattr
                                # If it's a dict (fallback), use .get()
                                if hasattr(resolved_value, part):
                                    resolved_value = getattr(resolved_value, part)
                                    # If it's a recordset, get the value if it's a single record
                                    # This handles many2one fields automatically
                                    if hasattr(resolved_value, 'id') and not parts[parts.index(part)+1:]:
                                        # If it's the last part and it's a record, we usually want the ID
                                        # But wait, usually domains ('partner_id', '=', user.partner_id) 
                                        # will work if resolved_value is the record.
                                        pass
                                elif isinstance(resolved_value, dict):
                                    resolved_value = resolved_value.get(part)
                                else:
                                    resolved_value = None
                                    break
                            else:
                                break
                                
                        if resolved_value is not None:
                            logger.debug(f"Resolved variable '{value}' to '{resolved_value}'")
                            resolved_domain.append((field, operator, resolved_value))
                        else:
                            logger.warning(f"Failed to resolve variable '{value}'")
                            # If resolution fails, we skip this criterion to avoid illegal queries
                    except Exception as e:
                        logger.error(f"Error resolving domain context for {value}: {e}")
                else:
                    resolved_domain.append(criterion)
            else:
                logger.warning(f"Invalid domain criterion encountered: {criterion}")
        
        logger.debug(f"Resolved domain: {resolved_domain}")
        return resolved_domain

    @staticmethod
    def apply_domain_filter(query, user, model_name):
        """Apply domain filter to SQLAlchemy query"""
        domain = PolicyEngine.get_domain_filter(user, model_name)
        if not domain:
            return query
            
        from backend.core.registry import registry
        model_cls = registry.get_model(model_name)
        if not model_cls:
            return query
            
        for field, operator, value in domain:
            if hasattr(model_cls, field):
                attr = getattr(model_cls, field)
                if operator == "=":
                    query = query.filter(attr == value)
                elif operator == "!=":
                    query = query.filter(attr != value)
                elif operator == "in":
                    if isinstance(value, (list, tuple)):
                        query = query.filter(attr.in_(value))
                elif operator == ">":
                    query = query.filter(attr > value)
                elif operator == "<":
                    query = query.filter(attr < value)
                elif operator == ">=":
                    query = query.filter(attr >= value)
                elif operator == "<=":
                    query = query.filter(attr <= value)
                elif operator == "ilike":
                    query = query.filter(attr.ilike(f"%{value}%"))
                    
        return query

    @staticmethod
    def get_visible_fields(user, model_cls):
        """Get visible fields for user role (kept for backward compatibility)"""
        metadata = model_cls._ui_metadata
        views = model_cls._ui_views
        
        if not user or not user.role:
            return {"fields": {}, "views": {}}
            
        role_name = user.role.name
        if role_name == RoleName.ADMIN:
            return {"fields": metadata, "views": views}
            
        # Filter fields for normal users based on roles (if field-level roles exist)
        visible_metadata = {}
        for field, config in metadata.items():
            roles_allowed = config.get("roles", [])
            if not roles_allowed or role_name in roles_allowed:
                visible_metadata[field] = config
        
        return {"fields": visible_metadata, "views": views}

policy_engine = PolicyEngine()
