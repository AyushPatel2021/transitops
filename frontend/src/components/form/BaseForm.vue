<template>
  <div class="base-form-pivot">
    <!-- Mobile Header (Znova Style) -->
    <div v-if="isMobile" class="mobile-header-znova">
      <div class="mobile-header-content">
        <!-- Left: Back button and Title -->
        <div class="mobile-left-section">
          <button class="mobile-back-btn" @click="$emit('breadcrumb-click', breadcrumbs[breadcrumbs.length - 2], breadcrumbs.length - 2)" v-if="breadcrumbs.length > 1">
            <ArrowLeft class="icon-sm" />
          </button>
          <span class="page-title">{{ modelName }}</span>
        </div>
        
        <!-- Right: Action buttons -->
        <div class="mobile-actions">
          <button class="mobile-action-btn" @click="showSmartButtons = !showSmartButtons" v-if="viewDefinition?.smart_buttons?.length || viewDefinition?.header_buttons?.length || (formData.id && actionPermissions.showDeleteButton)">
            <Settings class="icon-sm" />
          </button>
            <div class="mobile-pager-btns" v-if="totalInPage > 0">
            <button class="mobile-btn-pager" @click="$emit('nav', 'prev')">
              <ChevronLeft class="icon-sm" />
            </button>
            <button class="mobile-btn-pager" @click="$emit('nav', 'next')">
              <ChevronRight class="icon-sm" />
            </button>
          </div>
        </div>
      </div>
      
      <!-- Smart Buttons Dropdown -->
      <div v-if="showSmartButtons && (viewDefinition?.smart_buttons?.length || viewDefinition?.header_buttons?.length || (formData.id && actionPermissions.showDeleteButton))" class="mobile-smart-dropdown">
        <!-- Smart Buttons Section -->
        <div v-if="viewDefinition?.smart_buttons?.length" class="dropdown-section">
          <div class="section-header">Smart Actions</div>
          <div 
            v-for="btn in (viewDefinition.smart_buttons || []).filter((b: any) => isButtonVisible(b))" 
            :key="btn.name"
            class="smart-button-item"
            @click="onBtnAction(btn); showSmartButtons = false;"
          >
            <Zap class="icon-sm" />
            <span>{{ btn.label }}</span>
          </div>
        </div>
        
        <!-- Header Buttons Section -->
        <div v-if="viewDefinition?.header_buttons?.length && formData.id" class="dropdown-section">
          <div class="section-header">Actions</div>
          <div 
            v-for="btn in (viewDefinition.header_buttons || []).filter((b: any) => isButtonVisible(b))" 
            :key="btn.name"
            class="smart-button-item"
            @click="onBtnAction(btn); showSmartButtons = false;"
          >
            <Settings class="icon-sm" />
            <span>{{ btn.label }}</span>
          </div>
        </div>

        <!-- Destructive Actions Section -->
        <div v-if="formData.id && actionPermissions.showDeleteButton" class="dropdown-section">
          <div class="section-header">Destructive</div>
          <div 
            class="smart-button-item group-danger"
            @click="handleDeleteRequest(); showSmartButtons = false;"
          >
            <Trash2 class="icon-sm text-danger" />
            <span class="text-danger">Delete {{ modelName }}</span>
          </div>
        </div>
      </div>
      
      <!-- Mobile Action Row -->
      <div class="mobile-action-row">
        <!-- Save/Discard buttons (only show if user has permissions) -->
        <div class="mobile-save-actions" v-if="(isDirty || !formData.id) && actionPermissions.showSaveButton">
          <button class="btn btn-secondary mobile-action-btn-small" @click="handleDiscard" v-if="actionPermissions.showDiscardButton">
            Discard
          </button>
          <button class="btn btn-primary mobile-action-btn-small" @click="handleSave()" v-if="actionPermissions.allowFormSubmission">
            Save
          </button>
        </div>
        
        <!-- Empty space when no save/discard buttons -->
        <div v-else class="mobile-empty-space"></div>
        
        <!-- Pagination info -->
        <div class="mobile-pagination-info" v-if="totalInPage > 0">
          <span class="page-info">{{ currentIndex + 1 }} / {{ totalInPage }}</span>
        </div>
      </div>
    </div>

    <!-- Desktop Action Bar (Reference Framework Style) -->
    <div v-else class="action-bar">
      <div class="action-bar-left">
        <button class="btn btn-primary" @click="$emit('create')" v-if="actionPermissions.showCreateButton">
          <span>New</span>
        </button>
      </div>
      
      <div class="action-bar-right">
        <div class="pager-wrapper" v-if="totalInPage > 0">
          <div class="nav-arrows">
            <button class="nav-arrow" @click="$emit('nav', 'prev')" title="Previous Page">
              <ChevronLeft class="icon-sm" />
            </button>
            <button class="nav-arrow" @click="$emit('nav', 'next')" title="Next Page">
              <ChevronRight class="icon-sm" />
            </button>
          </div>
          <span class="pager-info">{{ currentIndex + 1 }} / {{ totalInPage }}</span>
        </div>
      </div>
    </div>

    <!-- Main Sheet Area -->
    <div class="sheet-viewport">
      <!-- Loading State -->
      <div v-if="loading || !metadata" class="integrated-content-wrapper">
        <div class="form-content-scrollable">
          <div :class="[isMobile ? 'form-sheet-mobile' : 'form-sheet-expanded']">
            <FormSkeleton />
          </div>
        </div>
      </div>
      
      <div v-else class="integrated-content-wrapper">
        <div class="form-main-content">
        <!-- Actions & Status Bar - Fixed within content area -->
        <div v-if="!isMobile" class="status-bar-integrated">
          <div class="status-left">
            <div class="action-buttons">
              <!-- Save/Discard shown ONLY if dirty or new AND user has permissions -->
              <template v-if="(isDirty || !formData.id) && actionPermissions.showSaveButton">
                <button class="btn btn-primary" @click="handleSave()" v-if="actionPermissions.allowFormSubmission">Save</button>
                <button class="btn btn-secondary" @click="handleDiscard" v-if="actionPermissions.showDiscardButton">Discard</button>
              </template>
              
              <!-- Header Buttons shown ONLY if record exists AND user has permissions -->
              <template v-if="formData.id && actionPermissions.showEditActions">
                <template v-for="btn in (viewDefinition?.header_buttons || []).filter((b: any) => isButtonVisible(b))" :key="btn.name">
                  <button 
                    :class="['btn', btn.type === 'primary' ? 'btn-primary' : 'btn-secondary']"
                    @click="onBtnAction(btn)"
                  >
                    {{ btn.label }}
                  </button>
                </template>
              </template>

              <!-- Action: Delete -->
              <button 
                v-if="formData.id && actionPermissions.showDeleteButton" 
                class="btn btn-danger" 
                @click="handleDeleteRequest"
              >
                <Trash2 class="icon-sm" />
                <span>Delete</span>
              </button>
            </div>
          </div>

          <div class="status-center">
            <SmartButtons 
              :buttons="(viewDefinition?.smart_buttons || []).filter((btn: any) => isButtonVisible(btn))" 
              :data="formData"
              @action="onBtnAction"
            />
          </div>

          <div class="status-right" v-if="getStatusField() && isFieldVisible(getStatusField())">
            <StatusBar 
              v-if="getStatusOptions().length"
              :stages="getStatusOptions()" 
              :currentValue="formData[getStatusField()] && typeof formData[getStatusField()] === 'object' ? formData[getStatusField()].id : formData[getStatusField()]"
              :readonly="isFieldReadonly(getStatusField()) || actionPermissions.makeFieldsReadonly"
              @change="handleStatusChange"
            />
          </div>
        </div>

        <!-- Scrollable Form Content -->
        <div class="form-content-scrollable">
        <div class="form-sheet-expanded">
        <!-- Header: Record Title -->
        <!-- Header: Record Title -->
        <div class="sheet-header" v-if="headerFields.length > 0">
           <div class="header-main-title">
             <!-- Title/Main Fields (Left Side) -->
             <div class="header-title-section">
               <template v-for="key in getVisibleFields(headerFields.filter((k: string) => allFields[k]?.type !== 'image'))" :key="key">
                 <!-- Priority Stars if widget is priority -->
                 <div v-if="allFields[key]?.widget === 'priority'" class="header-priority-top">
                   <PriorityField 
                      v-model="formData[key]"
                      :readonly="actionPermissions.makeFieldsReadonly"
                   />
                 </div>
                 
                 <!-- Other fields as Title style -->
                 <div v-else class="header-title">
                   <label class="model-label">{{ allFields[key]?.label }}</label>
                   
                   <!-- Show as display value when readonly -->
                   <h1 v-if="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly" class="title-display">
                     {{ formatValue(formData[key], allFields[key]?.type, allFields[key]) || '—' }}
                   </h1>
                   
                   <!-- Show as editable field when not readonly -->
                   <template v-else>
                     <!-- Special handling for Char/Text in header to make it look like a Title -->
                     <textarea 
                       v-if="allFields[key]?.type === 'char' || allFields[key]?.type === 'text'"
                       ref="titleTextArea"
                       :value="formData[key]" 
                       class="title-input" 
                       :placeholder="allFields[key]?.label.toUpperCase()" 
                       rows="1"
                       :class="{ 
                         'field-invalid': showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])
                       }"
                       @input="(e: any) => { autoResizeTitle(); handleValueChange(key, e.target.value, allFields[key].type); }"
                     ></textarea>
                     
                     <!-- For other types in header, render their specific components but with header styling -->
                     <div v-else class="header-widget-wrapper">
                        <SelectionField 
                            v-if="allFields[key]?.type === 'selection'"
                            :modelValue="formData[key]" 
                            :options="getOptions(allFields[key])"
                            :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                            :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                            class="header-selection"
                            @update:modelValue="(val: any) => handleValueChange(key, val, 'selection')"
                        />
                        <Many2OneField 
                            v-else-if="allFields[key]?.type === 'many2one'"
                            :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                            :options="getOptions(allFields[key], key)"
                            :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                            :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                            :relation="allFields[key].relation"
                            class="header-many2one"
                            @update:modelValue="(val: any) => handleValueChange(key, val, 'many2one')"
                            @focus="handleRelationFocus(allFields[key].relation, key)"
                        />
                        <DateField 
                            v-else-if="allFields[key]?.type === 'date'"
                            :modelValue="formData[key]"
                            :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                            :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                            class="header-date"
                            @update:modelValue="(val: any) => handleValueChange(key, val, 'date')"
                        />
                        <!-- Fallback for other types -->
                        <div v-else class="field-wrapper header-fallback">
                           <component 
                              :is="getEditComponent(allFields[key])" 
                              :value="formData[key]" 
                              v-bind="getEditProps(allFields[key])"
                              @input="(e: any) => handleValueChange(key, e.target.value, allFields[key].type)"
                              :class="{ 'field-invalid': showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key]) }"
                           />
                        </div>
                     </div>
                   </template>
                 </div>
               </template>
             </div>
           
             <!-- Header Image Fields (Right Side) -->
             <div class="header-image-section">
               <template v-for="key in getVisibleFields(headerFields.filter((k: string) => allFields[k]?.type === 'image'))" :key="key">
                 <div class="header-image">
                   <ImageField 
                      :modelValue="formData[key]"
                      :label="allFields[key]?.label"
                      :metadata="allFields[key]"
                      :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                      :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                      @update:modelValue="(val: any) => handleValueChange(key, val, 'image')"
                   />
                 </div>
               </template>
             </div>
           </div>
        </div>

        <!-- Groups Area -->
        <div class="sheet-grid" :class="{ 
          'mobile-layout': isMobile, 
          'tablet-layout': isTablet,
          'has-right-sidebar': hasRightSidebarGroups
        }">
          <!-- Main content groups (when no right sidebar) -->
          <template v-if="!hasRightSidebarGroups">
            <div v-for="group in getMainGroups()" :key="group.title" class="grid-column">
              <h3 class="group-title">{{ group.title }}</h3>
              <div 
                v-for="key in getVisibleFields(group.fields)" 
                :key="key" 
                class="field-item" 
                :class="{ 
                  'mobile-field': isMobile,
                  'no-label': allFields[key]?.show_label === false
                }"
                v-show="allFields[key]?.widget !== 'priority'"
              >
                <label v-if="allFields[key]?.show_label !== false" :class="{ 'required-label': isFieldRequired(key) }">
                  {{ allFields[key]?.label }}
                </label>
                <div class="field-wrapper" :style="{ minHeight: touchTargetSize.minHeight }">
                  <!-- Show as display value when readonly for simple fields only (NOT many2one - it needs to be clickable) -->
                  <div v-if="(isFieldReadonly(key) || actionPermissions.makeFieldsReadonly) && !['one2many', 'many2many', 'many2one', 'attachment', 'attachments'].includes(allFields[key]?.type)" class="view-value">
                    {{ formatValue(formData[key], allFields[key]?.type, allFields[key]) }}
                  </div>
                  <!-- Show as editable field when not readonly OR for complex fields that need proper rendering -->
                  <template v-else>
                    <One2manyField 
                        v-if="allFields[key]?.type === 'one2many'"
                        :ref="(el: any) => setOne2manyRef(key, el)"
                        :modelValue="formData[key] || []"
                        :metadata="allFields[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :context="formData"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'one2many')"
                        @error="() => {}"
                    />
                    <Many2manyField 
                        v-else-if="allFields[key]?.type === 'many2many'"
                        :ref="(el: any) => setMany2manyRef(key, el)"
                        :modelValue="formData[key] || []"
                        :metadata="allFields[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :context="formData"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'many2many')"
                        @error="() => {}"
                    />
                    <Many2OneField 
                        v-else-if="allFields[key]?.type === 'many2one'"
                        :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                        :options="getOptions(allFields[key], key)"
                        :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :relation="allFields[key].relation"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'many2one')"
                        @focus="handleRelationFocus(allFields[key].relation, key)"
                    />
                    <SelectionField 
                        v-else-if="allFields[key]?.type === 'selection'"
                        :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                        :options="getOptions(allFields[key])"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'selection')"
                    />
                    <DateField 
                        v-else-if="allFields[key]?.type === 'date'"
                        :modelValue="formData[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'date')"
                    />
                    <DateTimeField 
                        v-else-if="allFields[key]?.type === 'datetime'"
                        :modelValue="formData[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'datetime')"
                    />
                    <BooleanField 
                        v-else-if="allFields[key]?.type === 'boolean'"
                        :modelValue="formData[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'boolean')"
                    />
                    <PasswordField 
                        v-else-if="allFields[key]?.type === 'password'"
                        :modelValue="formData[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :showRequirements="true"
                        :placeholder="allFields[key]?.label"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'password')"
                    />
                    <ImageField 
                        v-else-if="allFields[key]?.type === 'image'"
                        :modelValue="formData[key]"
                        :label="allFields[key]?.label"
                        :metadata="allFields[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'image')"
                        @error="() => {}"
                    />
                    <AttachmentField 
                        v-else-if="allFields[key]?.type === 'attachment'"
                        :modelValue="formData[key]"
                        :metadata="{ ...allFields[key], name: key }"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :context="{ model: modelName, id: formData.id }"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'attachment')"
                    />
                    <AttachmentsField 
                        v-else-if="allFields[key]?.type === 'attachments'"
                        :modelValue="formData[key] || []"
                        :metadata="{ ...allFields[key], name: key }"
                        :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :context="{ model: modelName, id: formData.id }"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'attachments')"
                    />
                    <component 
                        v-else
                        :is="getEditComponent(allFields[key])" 
                        :value="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                        @input="(e: any) => handleValueChange(key, e.target.value, allFields[key].type)"
                        @focus="(e: any) => {}"
                        @blur="(e: any) => {}"
                        @mousedown="(e: any) => { e.stopPropagation(); }"
                        v-bind="getEditProps(allFields[key])"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :class="{ 
                          'field-invalid': showValidationErrors && isFieldRequired(key) && !formData[key]
                        }"
                        :style="{ minHeight: touchTargetSize.minHeight }"
                    />
                  </template>
                </div>
              </div>
            </div>
          </template>
          
          <!-- Left and center columns (when right sidebar exists) -->
          <div v-else class="main-content">
            <template v-if="viewDefinition?.groups?.length">
              <div v-for="group in getMainGroups()" :key="group.title" class="grid-column">
                <h3 class="group-title">{{ group.title }}</h3>
                <div 
                  v-for="key in getVisibleFields(group.fields)" 
                  :key="key" 
                  class="field-item" 
                  :class="{ 
                    'mobile-field': isMobile,
                    'no-label': allFields[key]?.show_label === false
                  }"
                  v-show="allFields[key]?.widget !== 'priority'"
                >
                  <label v-if="allFields[key]?.show_label !== false" :class="{ 'required-label': isFieldRequired(key) }">
                    {{ allFields[key]?.label }}
                  </label>
                  <div class="field-wrapper" :style="{ minHeight: touchTargetSize.minHeight }">
                    <!-- Show as display value when readonly for simple fields only (NOT many2one - it needs to be clickable) -->
                    <div v-if="(isFieldReadonly(key) || actionPermissions.makeFieldsReadonly) && !['one2many', 'many2many', 'many2one', 'attachment', 'attachments'].includes(allFields[key]?.type)" class="view-value">
                      {{ formatValue(formData[key], allFields[key]?.type, allFields[key]) }}
                    </div>
                    <!-- Show as editable field when not readonly OR for complex fields that need proper rendering -->
                    <template v-else>
                      <One2manyField 
                          v-if="allFields[key]?.type === 'one2many'"
                          :ref="(el: any) => setOne2manyRef(key, el)"
                          :modelValue="formData[key] || []"
                          :metadata="allFields[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :context="formData"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'one2many')"
                          @error="() => {}"
                      />
                      <Many2manyField 
                          v-else-if="allFields[key]?.type === 'many2many'"
                          :ref="(el: any) => setMany2manyRef(key, el)"
                          :modelValue="formData[key] || []"
                          :metadata="allFields[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :context="formData"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'many2many')"
                          @error="() => {}"
                      />
                      <Many2OneField 
                          v-else-if="allFields[key]?.type === 'many2one'"
                          :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                          :options="getOptions(allFields[key], key)"
                          :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :relation="allFields[key].relation"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'many2one')"
                          @focus="handleRelationFocus(allFields[key].relation, key)"
                      />
                      <SelectionField 
                          v-else-if="allFields[key]?.type === 'selection'"
                          :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                          :options="getOptions(allFields[key])"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'selection')"
                      />
                      <DateField 
                          v-else-if="allFields[key]?.type === 'date'"
                          :modelValue="formData[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'date')"
                      />
                      <DateTimeField 
                          v-else-if="allFields[key]?.type === 'datetime'"
                          :modelValue="formData[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'datetime')"
                      />
                      <BooleanField 
                          v-else-if="allFields[key]?.type === 'boolean'"
                          :modelValue="formData[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'boolean')"
                      />
                      <PasswordField 
                          v-else-if="allFields[key]?.type === 'password'" 
                          :modelValue="formData[key]" 
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]" 
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly" 
                          :showRequirements="true" 
                          :placeholder="allFields[key]?.label" 
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'password')" 
                      />
                      <ImageField 
                          v-else-if="allFields[key]?.type === 'image'"
                          :modelValue="formData[key]"
                          :label="allFields[key]?.label"
                          :metadata="allFields[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'image')"
                          @error="() => {}"
                      />
                      <component 
                          v-else
                          :is="getEditComponent(allFields[key])" 
                          :value="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                          @input="(e: any) => handleValueChange(key, e.target.value, allFields[key].type)"
                          @focus="(e: any) => {}"
                          @blur="(e: any) => {}"
                          @mousedown="(e: any) => { e.stopPropagation(); }"
                          v-bind="getEditProps(allFields[key])"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :class="{ 
                            'field-invalid': showValidationErrors && isFieldRequired(key) && !formData[key]
                          }"
                          :style="{ minHeight: touchTargetSize.minHeight }"
                      />
                    </template>
                  </div>
                </div>
              </div>
            </template>
          </div>
          
          <!-- Right sidebar for right-positioned groups -->
          <div v-if="hasRightSidebarGroups" class="right-sidebar">
            <template v-for="group in getRightSidebarGroups()" :key="group.title">
              <div class="sidebar-group" :style="{ width: group.width || '300px' }">
                <h3 class="group-title">{{ group.title }}</h3>
                <div 
                  v-for="key in getVisibleFields(group.fields)" 
                  :key="key" 
                  class="sidebar-field-item"
                >
                  <!-- Show as display value when readonly for simple fields only (NOT many2one - it needs to be clickable) -->
                  <div v-if="(isFieldReadonly(key) || actionPermissions.makeFieldsReadonly) && !['one2many', 'many2many', 'many2one', 'attachment', 'attachments'].includes(allFields[key]?.type)" class="view-value">
                    {{ formatValue(formData[key], allFields[key]?.type, allFields[key]) }}
                  </div>
                  <!-- Show as editable field when not readonly OR for complex fields that need proper rendering -->
                  <template v-else>
                    <ImageField 
                        v-if="allFields[key]?.type === 'image'"
                        :modelValue="formData[key]"
                        :label="allFields[key]?.label"
                        :metadata="allFields[key]"
                        :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        @update:modelValue="(val: any) => handleValueChange(key, val, 'image')"
                        @error="() => {}"
                    />
                    <!-- Add other field types as needed for sidebar -->
                  </template>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Tabs Area -->
        <div class="sheet-tabs" v-if="viewDefinition?.tabs?.length">
          <div class="tabs-header" :class="{ 'mobile-tabs': isMobile }">
            <div 
              v-for="tab in viewDefinition.tabs" 
              :key="tab.title"
              v-show="!tab.invisible || !evaluateDomain(tab.invisible, false)"
              :class="['tab-item', { 
                active: activeTab === tab.title,
                'invalid-tab': isTabInvalid(tab)
              }]"
              @click="activeTab = tab.title"
              :style="{ minHeight: touchTargetSize.minHeight }"
            >
              {{ tab.title }}
            </div>
          </div>
          <div class="tab-content">
            <!-- Render all tab fields but show only active tab fields -->
            <template v-for="tab in viewDefinition.tabs" :key="tab.title">
              <div v-if="activeTab === tab.title && (!tab.invisible || !evaluateDomain(tab.invisible, false))" class="tab-pane">
                <!-- Helper to render a list of fields -->
                <template v-if="tab.groups">
                  <div class="sheet-grid" :class="{ 
                    'mobile-layout': isMobile, 
                    'tablet-layout': isTablet,
                    'single-column': tab.groups.length === 1
                  }">
                    <div v-for="group in tab.groups" :key="group.title" class="grid-column">
                      <h3 v-if="group.title" class="group-title">{{ group.title }}</h3>
                        <template v-for="key in getVisibleFields(group.fields)" :key="`${tab.title}-${group.title}-${key}`">
                          <!-- Field Rendering Logic (Duplicated for now to be safe) -->
                          <div 
                            class="field-item" 
                            :class="{ 
                              'mobile-field': isMobile,
                              'no-label': allFields[key]?.show_label === false,
                              'full-width-field': ['attachments', 'attachment'].includes(allFields[key]?.type)
                            }" 
                            v-show="allFields[key]?.widget !== 'priority'"
                          >
                            <label v-if="allFields[key]?.type !== 'text' && allFields[key]?.show_label !== false" :class="{ 'required-label': isFieldRequired(key) }">
                              {{ allFields[key]?.label }}
                            </label>
                            <div :class="[allFields[key]?.type === 'text' ? 'full-field-text' : 'field-wrapper']" :style="{ minHeight: touchTargetSize.minHeight }">
                              <!-- Show as display value when readonly for simple fields only (NOT many2one - it needs to be clickable) -->
                              <div v-if="(isFieldReadonly(key) || actionPermissions.makeFieldsReadonly) && !['one2many', 'many2many', 'many2one', 'attachment', 'attachments'].includes(allFields[key]?.type)" class="view-value">
                                {{ formatValue(formData[key], allFields[key]?.type, allFields[key]) }}
                              </div>
                              <!-- Show as editable field when not readonly OR for complex fields that need proper rendering -->
                              <template v-else>
                                <textarea 
                                  v-if="allFields[key]?.type === 'text'" 
                                  v-model="formData[key]" 
                                  rows="5" 
                                  :placeholder="allFields[key].label" 
                                  class="form-text-area"
                                  :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                  :class="{ 
                                    'field-invalid': showValidationErrors && isFieldRequired(key) && !formData[key]
                                  }"
                                  :style="{ minHeight: isTouchDevice ? '120px' : '100px' }"
                                  @focus="(e: any) => {}"
                                  @blur="(e: any) => {}"
                                  @mousedown="(e: any) => { e.stopPropagation(); }"
                                ></textarea>
                                <One2manyField 
                                    v-else-if="allFields[key]?.type === 'one2many'"
                                    :ref="(el: any) => setOne2manyRef(key, el)"
                                    :modelValue="formData[key] || []"
                                    :metadata="allFields[key]"
                                    :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    :context="formData"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'one2many')"
                                    @error="() => {}"
                                />
                                <Many2manyField 
                                    v-else-if="allFields[key]?.type === 'many2many'"
                                    :ref="(el: any) => setMany2manyRef(key, el)"
                                    :modelValue="formData[key] || []"
                                    :metadata="allFields[key]"
                                    :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    :context="formData"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'many2many')"
                                    @error="() => {}"
                                />
                                <Many2OneField 
                                    v-else-if="allFields[key]?.type === 'many2one'"
                                    :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                                    :options="getOptions(allFields[key], key)"
                                    :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    :relation="allFields[key].relation"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'many2one')"
                                    @focus="handleRelationFocus(allFields[key].relation, key)"
                                />
                                <SelectionField 
                                    v-else-if="allFields[key]?.type === 'selection'"
                                    :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                                    :options="getOptions(allFields[key])"
                                    :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'selection')"
                                />
                                <DateField 
                                    v-else-if="allFields[key]?.type === 'date'"
                                    :modelValue="formData[key]"
                                    :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'date')"
                                />
                                <DateTimeField 
                                    v-else-if="allFields[key]?.type === 'datetime'"
                                    :modelValue="formData[key]"
                                    :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'datetime')"
                                />
                                <BooleanField 
                                    v-else-if="allFields[key]?.type === 'boolean'"
                                    :modelValue="formData[key]"
                                    :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'boolean')"
                                />
                                <PasswordField 
                                    v-else-if="allFields[key]?.type === 'password'" 
                                    :modelValue="formData[key]" 
                                    :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]" 
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly" 
                                    :showRequirements="true" 
                                    :placeholder="allFields[key]?.label" 
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'password')" 
                                />
                                <ImageField 
                                    v-else-if="allFields[key]?.type === 'image'"
                                    :modelValue="formData[key]"
                                    :label="allFields[key]?.label"
                                    :metadata="allFields[key]"
                                    :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'image')"
                                    @error="() => {}"
                                />
                                <AttachmentField 
                                    v-else-if="allFields[key]?.type === 'attachment'"
                                    :modelValue="formData[key]"
                                    :metadata="{ ...allFields[key], name: key }"
                                    :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    :context="{ model: modelName, id: formData.id }"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'attachment')"
                                />
                                <AttachmentsField 
                                    v-else-if="allFields[key]?.type === 'attachments'"
                                    :modelValue="formData[key] || []"
                                    :metadata="{ ...allFields[key], name: key }"
                                    :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                                    :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                    :context="{ model: modelName, id: formData.id }"
                                    @update:modelValue="(val: any) => handleValueChange(key, val, 'attachments')"
                                />
                                <component 
                                  v-else
                                  :is="getEditComponent(allFields[key])" 
                                  :value="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                                  @input="(e: any) => handleValueChange(key, e.target.value, allFields[key].type)"
                                  @focus="(e: any) => {}"
                                  @blur="(e: any) => {}"
                                  @mousedown="(e: any) => { e.stopPropagation(); }"
                                  v-bind="getEditProps(allFields[key])"
                                  :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                                  :class="{ 
                                    'field-invalid': showValidationErrors && isFieldRequired(key) && !formData[key]
                                  }"
                                  :style="{ minHeight: touchTargetSize.minHeight }"
                                />
                              </template>
                            </div>
                          </div>
                          <!-- End Field Rendering Logic -->
                        </template>
                    </div>
                  </div>
                </template>

                <template v-else-if="tab.fields">
                  <template v-for="key in getVisibleFields(tab.fields)" :key="`${tab.title}-${key}`">
                    <div 
                      class="field-item" 
                      :class="{ 
                        'mobile-field': isMobile,
                        'no-label': allFields[key]?.show_label === false,
                        'full-width-field': ['attachments', 'attachment'].includes(allFields[key]?.type)
                      }" 
                      v-show="allFields[key]?.widget !== 'priority'"
                    >
                      <label v-if="allFields[key]?.type !== 'text' && allFields[key]?.show_label !== false" :class="{ 'required-label': isFieldRequired(key) }">
                        {{ allFields[key]?.label }}
                      </label>

                  <div :class="[allFields[key]?.type === 'text' ? 'full-field-text' : 'field-wrapper']" :style="{ minHeight: touchTargetSize.minHeight }">
                    <!-- Show as display value when readonly for simple fields only (NOT many2one - it needs to be clickable) -->
                    <div v-if="(isFieldReadonly(key) || actionPermissions.makeFieldsReadonly) && !['one2many', 'many2many', 'many2one', 'attachment', 'attachments'].includes(allFields[key]?.type)" class="view-value">
                      {{ formatValue(formData[key], allFields[key]?.type, allFields[key]) }}
                    </div>
                    <!-- Show as editable field when not readonly OR for complex fields that need proper rendering -->
                    <template v-else>
                      <textarea 
                        v-if="allFields[key]?.type === 'text'" 
                        v-model="formData[key]" 
                        rows="5" 
                        :placeholder="allFields[key].label" 
                        class="form-text-area"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :class="{ 
                          'field-invalid': showValidationErrors && isFieldRequired(key) && !formData[key]
                        }"
                        :style="{ minHeight: isTouchDevice ? '120px' : '100px' }"
                        @focus="(e: any) => {}"
                        @blur="(e: any) => {}"
                        @mousedown="(e: any) => { e.stopPropagation(); }"
                      ></textarea>
                      <One2manyField
                          v-else-if="allFields[key]?.type === 'one2many'"
                          :ref="(el: any) => setOne2manyRef(key, el)"
                          :modelValue="formData[key] || []"
                          :metadata="allFields[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :context="formData"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'one2many')"
                          @error="() => {}"
                      />
                      <Many2manyField
                          v-else-if="allFields[key]?.type === 'many2many'"
                          :ref="(el: any) => setMany2manyRef(key, el)"
                          :modelValue="formData[key] || []"
                          :metadata="allFields[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :context="formData"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'many2many')"
                          @error="() => {}"
                      />
                      <Many2OneField 
                          v-else-if="allFields[key]?.type === 'many2one'"
                          :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                          :options="getOptions(allFields[key], key)"
                          :invalid="showValidationErrors && isFieldRequired(key) && isFieldEmpty(formData[key])"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :relation="allFields[key].relation"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'many2one')"
                          @focus="handleRelationFocus(allFields[key].relation, key)"
                      />
                      <SelectionField 
                          v-else-if="allFields[key]?.type === 'selection'"
                          :modelValue="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                          :options="getOptions(allFields[key])"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'selection')"
                      />
                      <DateField 
                          v-else-if="allFields[key]?.type === 'date'"
                          :modelValue="formData[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'date')"
                      />
                      <DateTimeField 
                          v-else-if="allFields[key]?.type === 'datetime'"
                          :modelValue="formData[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'datetime')"
                      />
                      <BooleanField 
                          v-else-if="allFields[key]?.type === 'boolean'"
                          :modelValue="formData[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'boolean')"
                      />
                      <PasswordField 
                          v-else-if="allFields[key]?.type === 'password'" 
                          :modelValue="formData[key]" 
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]" 
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly" 
                          :showRequirements="true" 
                          :placeholder="allFields[key]?.label" 
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'password')" 
                      />
                      <ImageField 
                          v-else-if="allFields[key]?.type === 'image'"
                          :modelValue="formData[key]"
                          :label="allFields[key]?.label"
                          :metadata="allFields[key]"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'image')"
                          @error="() => {}"
                      />
                      <AttachmentField 
                          v-else-if="allFields[key]?.type === 'attachment'"
                          :modelValue="formData[key]"
                          :metadata="{ ...allFields[key], name: key }"
                          :invalid="showValidationErrors && isFieldRequired(key) && !formData[key]"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :context="{ model: modelName, id: formData.id }"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'attachment')"
                      />
                      <AttachmentsField 
                          v-else-if="allFields[key]?.type === 'attachments'"
                          :modelValue="formData[key] || []"
                          :metadata="{ ...allFields[key], name: key }"
                          :invalid="showValidationErrors && isFieldRequired(key) && (!formData[key] || formData[key].length === 0)"
                          :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                          :context="{ model: modelName, id: formData.id }"
                          @update:modelValue="(val: any) => handleValueChange(key, val, 'attachments')"
                      />
                      <component 
                        v-else
                        :is="getEditComponent(allFields[key])" 
                        :value="formData[key] && typeof formData[key] === 'object' ? formData[key].id : formData[key]" 
                        @input="(e: any) => handleValueChange(key, e.target.value, allFields[key].type)"
                        @focus="(e: any) => {}"
                        @blur="(e: any) => {}"
                        @mousedown="(e: any) => { e.stopPropagation(); }"
                        v-bind="getEditProps(allFields[key])"
                        :readonly="isFieldReadonly(key) || actionPermissions.makeFieldsReadonly"
                        :class="{ 
                          'field-invalid': showValidationErrors && isFieldRequired(key) && !formData[key]
                        }"
                        :style="{ minHeight: touchTargetSize.minHeight }"
                      />
                    </template>
                  </div>
                </div>
              </template>
              </template>
              </div>
            </template>
          </div>
        </div>
        </div>
        </div>
        </div>
      </div>
    </div>

    <!-- Audit Log Drawer (Floating, outside main content) -->
    <AuditLogSidebar
      v-if="showAuditSidebar && formData.id"
      :modelName="modelName"
      :recordId="formData.id"
      :visible="!isMobile || auditSidebarVisible"
      @close="auditSidebarVisible = false"
      ref="auditLogRef"
    />

    <!-- Reset Password Modal -->
    <ResetPasswordModal
      :isVisible="showResetPasswordModal"
      :userId="resetPasswordUserId"
      :userName="resetPasswordUserName"
      :userEmail="resetPasswordUserEmail"
      @close="closeResetPasswordModal"
      @success="handleResetPasswordSuccess"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
const showValidationErrors = ref(false);
import { 
  ChevronLeft, 
  ChevronRight,
  ArrowLeft,
  Settings,
  Zap,
  Trash2,
  Plus
} from 'lucide-vue-next';
import api from '../../core/api';
import Many2OneField from './Many2OneField.vue';
import One2manyField from './One2manyField.vue';
import Many2manyField from './Many2manyField.vue';
import SelectionField from './SelectionField.vue';
import DateField from './DateField.vue';
import DateTimeField from './DateTimeField.vue';
import ImageField from './ImageField.vue';
import BooleanField from './BooleanField.vue';
import PasswordField from './PasswordField.vue';
import AttachmentField from './AttachmentField.vue';
import AttachmentsField from './AttachmentsField.vue';
import SmartButtons from './SmartButtons.vue';
import StatusBar from './StatusBar.vue';
import Breadcrumbs from '../common/Breadcrumbs.vue';
import NotificationBell from '../common/NotificationBell.vue';
import PriorityField from './PriorityField.vue';
import FormSkeleton from '../skeleton/FormSkeleton.vue';
import ResetPasswordModal from '../modals/ResetPasswordModal.vue';
import AuditLogSidebar from '../audit/AuditLogSidebar.vue';
import { formatValue as formatValueUtil } from '../../utils/formatters';
import { formatDateTime, formatDate } from '../../utils/dateUtils';
import { useResponsive } from '../../composables/useResponsive';
import { useFieldVisibility } from '../../composables/useFieldVisibility';
import { useUnifiedPermissions } from '../../composables/useUnifiedPermissions';
import { useNotifications } from '../../composables/useNotifications';
import { useDialog } from '../../composables/useDialog';
import { DomainEngine } from '../../core/domain-engine';

const props = defineProps<{
  modelName: string;
  formData: any;
  metadata: any; 
  loading: boolean;
  saving?: boolean;
  error?: string | null;
  currentIndex: number;
  totalInPage: number;
  breadcrumbs: any[];
}>();

const emit = defineEmits(['save', 'cancel', 'create', 'logout', 'nav', 'breadcrumb-click', 'action', 'refresh']);

// Initialize responsive composable
const { isMobile, isTablet, isDesktop, isTouchDevice, formColumns, touchTargetSize } = useResponsive();

// Simple date formatting without timezone
const formatValue = (value: any, type: string, field: any) => {
    // Special handling for sequence fields (readonly fields with "New" default)
    if (field?.readonly && field?.default === "New") {
        // If the field has a real value (not null/undefined/empty), show it
        if (value && value !== "New") {
            return value;
        }
        // Otherwise show "New" for empty values
        if (value === null || value === undefined || value === "") {
            return "New";
        }
    }
    
    if (value === null || value === undefined) return '';
    if (type === 'boolean') return value ? 'Yes' : 'No';
    
    if (type === 'date' || type === 'datetime') {
        if (value && typeof value === 'string') {
            try {
                if (type === 'date') {
                    return formatDate(value);
                } else {
                    return formatDateTime(value);
                }
            } catch {
                // Ignore date parsing errors
            }
        }
        return value || '';
    }
    
    // Support object-based many2one values from backend or synced state
    if (type === 'many2one' && typeof value === 'object') {
        return value.display_name || value.name || value.full_name || value.id;
    }

    if (type === 'selection') {
        // Handle both array and object formats for selection options
        if (Array.isArray(field.selection)) {
            const option = field.selection.find(([val]: any) => val === value);
            return option ? option[1] : value;
        }
        if (field.options && typeof field.options === 'object') {
            const opt = field.options[value];
            return typeof opt === 'object' ? opt.label : opt;
        }
        return value;
    }
    
    if (type === 'many2one' && relations[field.relation]) {
        const rel = relations[field.relation].find((r: any) => r.id === value);
        return rel ? (rel.display_name || rel.name || rel.full_name || rel.subject) : `#${value}`;
    }
    
    if (type === 'many2many') {
        if (!Array.isArray(value)) return '';
        const names = value.map((item: any) => {
            if (typeof item === 'object') {
                return item.display_name || item.name || item.full_name || item.subject || `#${item.id}`;
            }
            return item;
        });
        return names.join(', ');
    }
    
    if (type === 'one2many') {
        if (!Array.isArray(value)) return '';
        const count = value.filter((item: any) => !item._deleted).length;
        return `${count} record${count !== 1 ? 's' : ''}`;
    }
    
    if (type === 'image') {
        return value ? 'Image uploaded' : 'No image';
    }
    
    if (type === 'password') {
        return value ? '••••••••' : '';
    }
    
    return value;
};

// Refs for relational field components (for validation)
const one2manyFieldRefs = ref<Map<string, any>>(new Map());
const many2manyFieldRefs = ref<Map<string, any>>(new Map());

// Helper to set relational field refs
const setOne2manyRef = (fieldName: string, el: any) => {
  if (el) {
    one2manyFieldRefs.value.set(fieldName, el);
  } else {
    one2manyFieldRefs.value.delete(fieldName);
  }
};

const setMany2manyRef = (fieldName: string, el: any) => {
  if (el) {
    many2manyFieldRefs.value.set(fieldName, el);
  } else {
    many2manyFieldRefs.value.delete(fieldName);
  }
};

// Create reactive copies of props for better reactivity
const reactiveFormData = reactive(props.formData || {});
const reactiveMetadata = reactive(props.metadata || {});

// Sync reactive copies with props
watch(() => props.formData, (newData) => {
  if (newData) {
    Object.assign(reactiveFormData, newData);
  }
}, { deep: true, immediate: true });

watch(() => props.metadata, (newMeta) => {
  if (newMeta) {
    Object.assign(reactiveMetadata, newMeta);
  }
}, { deep: true, immediate: true });

// Initialize field visibility composable with reactive data
const { 
  isFieldVisible, 
  isFieldReadonly, 
  isFieldRequired, 
  getVisibleFields,
  evaluateAllFields,
  evaluateDomain,
  forceLocalEvaluation,
  resetToBackendEvaluation,
  fieldStates 
} = useFieldVisibility(
  computed(() => reactiveMetadata),
  computed(() => reactiveFormData)
);

// Initialize unified permissions composable
const { 
  actionPermissions, 
  canCreate, 
  canWrite, 
  canDelete,
  getPermissionClasses,
  refreshPermissions 
} = useUnifiedPermissions(
  props.modelName, 
  computed(() => props.formData?.id || 'new')
);

const showSmartButtons = ref(false);
const showActionMenu = ref(false);

// Reset Password Modal state
const showResetPasswordModal = ref(false);
const resetPasswordUserId = ref(0);
const resetPasswordUserName = ref('');
const resetPasswordUserEmail = ref('');

const isButtonVisible = (btn: any) => {
    if (!btn) return false;

    if (btn.field) {
        const rawValue = props.formData?.[btn.field];
        if (rawValue === null || rawValue === undefined || rawValue === '' || rawValue === false) {
            return false;
        }
        if (typeof rawValue === 'number' && rawValue <= 0) {
            return false;
        }
        if (Array.isArray(rawValue) && rawValue.length === 0) {
            return false;
        }
    }

    if (!btn.invisible) return true;
    return !evaluateDomain(btn.invisible, false);
};

const handleDeleteRequest = () => {
    emit('action', { name: 'delete', label: 'Delete', type: 'object' });
};
const titleTextArea = ref<HTMLTextAreaElement | null>(null);

const autoResizeTitle = () => {
    if (titleTextArea.value) {
        titleTextArea.value.style.height = 'auto';
        titleTextArea.value.style.height = titleTextArea.value.scrollHeight + 'px';
    }
};

const allFields = computed(() => props.metadata?.fields || {});
const viewDefinition = computed(() => props.metadata?.views?.form || {});

// Audit log sidebar
const auditLogRef = ref(null);
const auditSidebarVisible = ref(false);
const showAuditSidebar = computed(() => {
  return viewDefinition.value?.show_audit_log === true;
});

const isDirty = computed(() => {
    if (!originalData.value || !props.formData) return false;
    
    // Check all metadata fields for changes
    for (const key of Object.keys(allFields.value)) {
        const field = allFields.value[key];
        const current = props.formData[key];
        const original = originalData.value[key];
        
        if (field?.type === 'many2one') {
            const curId = (current && typeof current === 'object') ? current.id : current;
            const origId = (original && typeof original === 'object') ? original.id : original;
            if (curId !== origId) return true;
            continue;
        }

        if (field?.type === 'one2many') {
            // Special handling for one2many fields
            const currentArray = Array.isArray(current) ? current : [];
            const originalArray = Array.isArray(original) ? original : [];
            
            // Filter out deleted records for comparison
            const currentActive = currentArray.filter(r => !r._deleted);
            const originalActive = originalArray.filter(r => !r._deleted);
            
            // Compare lengths first
            if (currentActive.length !== originalActive.length) return true;
            
            // Compare each record by ID and relevant fields
            for (let i = 0; i < currentActive.length; i++) {
                const curRecord = currentActive[i];
                const origRecord = originalActive[i];
                
                // If both have IDs, compare by ID
                if (curRecord.id && origRecord.id) {
                    if (curRecord.id !== origRecord.id) return true;
                    // Also check if existing record was modified
                    if (curRecord._modified) return true;
                } else if (curRecord._isNew !== origRecord._isNew) {
                    // New record status changed
                    return true;
                } else {
                    // Compare record contents (excluding temp fields)
                    const curClean = { ...curRecord };
                    const origClean = { ...origRecord };
                    delete curClean._tempId;
                    delete curClean._isNew;
                    delete curClean._modified;
                    delete origClean._tempId;
                    delete origClean._isNew;
                    delete origClean._modified;
                    
                    if (JSON.stringify(curClean) !== JSON.stringify(origClean)) return true;
                }
            }
            continue;
        }

        if (JSON.stringify(current) !== JSON.stringify(original)) return true;
    }
    return false;
});

const originalData = ref<any>(null);

onMounted(() => {
    if (props.formData && !props.loading) {
        originalData.value = JSON.parse(JSON.stringify(props.formData));
    }
});

onUnmounted(() => {
    // Component cleanup
});

watch(() => props.loading, (isLoading, wasLoading) => {
    // When loading finishes (true -> false), capture the initial state of the record
    // CRITICAL: Only update originalData if there was NO error. 
    // If an error occurred (e.g. UserError during save), we MUST keep isDirty=true.
    if (isLoading === false && !props.error) {
        if (props.formData) {
            originalData.value = JSON.parse(JSON.stringify(props.formData));
            // Reset to use backend domain evaluation when form is loaded/saved
            resetToBackendEvaluation();
        } else {
            originalData.value = {};
        }
    }
}, { immediate: true });

watch(() => props.modelName, () => {
    originalData.value = null; // Clear original data when model changes
});

const isFieldEmpty = (value: any): boolean => {
  if (value === null || value === undefined || value === '') return true;
  if (typeof value === 'object' && value !== null) {
    return value.id === null || value.id === undefined || value.id === '';
  }
  return false;
};

const triggerOnchange = async (fieldName: string) => {
    try {
        const response = await api.post(`/models/${props.modelName}/onchange`, {
            vals: props.formData,
            field_name: fieldName
        });
        
        if (response.data) {
            // Update formData and reactiveFormData with changes from backend
            Object.keys(response.data).forEach(k => {
                let newVal = response.data[k];
                
                // Normalization: Extract ID from object for many2one fields
                // Start with metadata check
                const fieldType = allFields.value[k]?.type;
                if (fieldType === 'many2one' && newVal && typeof newVal === 'object' && 'id' in newVal) {
                    newVal = newVal.id;
                }
                
                // Only update if value changed and it's not a temporary field
                if (!k.startsWith('_') && JSON.stringify(props.formData[k]) !== JSON.stringify(newVal)) {
                    props.formData[k] = newVal;
                    reactiveFormData[k] = newVal;
                }
            });
        }
    } catch (err) {
        console.error("Error triggering onchange:", err);
    }
};

// Debounced version for text fields to avoid API spam on every keystroke
let _onchangeTimer: ReturnType<typeof setTimeout> | null = null;
const triggerOnchangeDebounced = (fieldName: string) => {
    if (_onchangeTimer) clearTimeout(_onchangeTimer);
    _onchangeTimer = setTimeout(() => {
        triggerOnchange(fieldName);
    }, 500);
};

const handleValueChange = (key: string, value: any, type: string) => {
    if (type === 'many2one' || type === 'selection') {
        let val = value;
        if (value === 'null' || value === '' || value === null || value === undefined) {
            val = null;
        } else if (typeof value === 'string' && !isNaN(value as any)) {
            val = parseInt(value);
        }
        props.formData[key] = val;
        reactiveFormData[key] = val; // Update reactive copy
    } else if (type === 'integer') {
        // Parse as integer, reject decimals
        let val = value;
        if (value === '' || value === null || value === undefined) {
            val = null;
        } else {
            const parsed = parseInt(value, 10);
            val = isNaN(parsed) ? null : parsed;
        }
        props.formData[key] = val;
        reactiveFormData[key] = val;
    } else if (type === 'float') {
        // Parse as float
        let val = value;
        if (value === '' || value === null || value === undefined) {
            val = null;
        } else {
            const parsed = parseFloat(value);
            val = isNaN(parsed) ? null : parsed;
        }
        props.formData[key] = val;
        reactiveFormData[key] = val;
    } else if (type === 'one2many' || type === 'many2many') {
        // For relational fields, store the array directly
        props.formData[key] = value || [];
        reactiveFormData[key] = value || []; // Update reactive copy
    } else {
        props.formData[key] = value;
        reactiveFormData[key] = value; // Update reactive copy
    }
    
    // Trigger onchange if defined in metadata
    if (allFields.value[key]?.onchange) {
        // Use debounced version for text-like fields to avoid API spam
        if (type === 'char' || type === 'text' || type === 'integer' || type === 'float' || type === 'html') {
            triggerOnchangeDebounced(key);
        } else {
            triggerOnchange(key);
        }
    }
    
    // Force local domain evaluation immediately when form data changes
    nextTick(() => {
        forceLocalEvaluation();
    });
};

const handleStatusChange = (newStatus: any) => {
    const statusField = getStatusField();
    if (statusField) {
        props.formData[statusField] = newStatus;
        reactiveFormData[statusField] = newStatus; // Ensure reactivity for domains
        
        // Trigger onchange if defined for the status field
        if (allFields.value[statusField]?.onchange) {
            triggerOnchange(statusField);
        }
    }
};

const handleSave = (callback?: () => void) => {
    // Check permissions before saving
    if (!actionPermissions.value.allowFormSubmission) {
        // Save blocked: User does not have permission to save this record
        return;
    }
    
    // Validate relational fields first
    let relationalFieldsValid = true;
    const relationalErrors: string[] = [];
    
    // Validate one2many fields
    for (const [fieldName, fieldRef] of one2manyFieldRefs.value.entries()) {
        if (fieldRef && typeof fieldRef.validate === 'function') {
            const isValid = fieldRef.validate();
            if (!isValid) {
                relationalFieldsValid = false;
                const fieldLabel = allFields.value[fieldName]?.label || fieldName;
                relationalErrors.push(fieldLabel);
            }
        } else {
            // Silently skip validation for fields without validate method
        }
    }
    
    // Validate many2many fields
    for (const [fieldName, fieldRef] of many2manyFieldRefs.value.entries()) {
        if (fieldRef && typeof fieldRef.validate === 'function') {
            const isValid = fieldRef.validate();
            if (!isValid) {
                relationalFieldsValid = false;
                const fieldLabel = allFields.value[fieldName]?.label || fieldName;
                relationalErrors.push(fieldLabel);
            }
        }
    }
    
    // frontend validation for regular fields
    const missingFields = Object.keys(allFields.value).filter(key => {
        if (!isFieldRequired(key)) return false;
        return isFieldEmpty(props.formData[key]);
    });

    if (missingFields.length > 0 || !relationalFieldsValid) {
        showValidationErrors.value = true;
        
        // Find the first tab with validation errors and switch to it
        if (viewDefinition.value?.tabs?.length) {
            for (const tab of viewDefinition.value.tabs) {
                if (isTabInvalid(tab)) {
                    activeTab.value = tab.title;
                    break;
                }
            }
        }
        
        // Combine all validation errors
        const allErrors = [...missingFields, ...relationalErrors];
        const fieldLabels = allErrors.map(key => {
            // If it's already a label (from relational errors), use it directly
            if (relationalErrors.includes(key)) return key;
            // Otherwise, get the label from metadata
            return allFields.value[key]?.label || key;
        });
        
        const message = `Please fill in the following required fields: ${fieldLabels.join(', ')}`;
        
        // Import and use notifications
        const { add } = useNotifications();
        add({
            title: 'Validation Error',
            message: message,
            type: 'danger',
            duration: 5000,
            sticky: false
        });
        
        return;
    }
    
    showValidationErrors.value = false;
    
    // Process relational fields before saving
    const payload = processRelationalFields({ ...props.formData });
    
    emit('save', payload, callback);
};

const processRelationalFields = (data: any) => {
    const payload = { ...data };
    
    // Process one2many fields
    for (const [fieldName, fieldMeta] of Object.entries(allFields.value)) {
        if (!fieldMeta || typeof fieldMeta !== 'object') continue;
        
        if ((fieldMeta as any)['type'] === 'one2many') {
            const records = data[fieldName] || [];
            if (!Array.isArray(records)) continue;

            const operations: any = {
                create: [],
                update: [],
                delete: []
            };
            
            // Track original IDs if this is an update
            const originalIds = originalData.value?.[fieldName]?.map((r: any) => r.id).filter((id: any) => id) || [];
            const currentIds: number[] = [];
            
            records.forEach((record: any) => {
                if (record._deleted) {
                    // Mark for deletion
                    if (record.id) {
                        operations.delete.push(record.id);
                    }
                } else if (record._isNew || !record.id) {
                    // New record - create
                    const cleanRecord = { ...record };
                    delete cleanRecord._tempId;
                    delete cleanRecord._isNew;
                    delete cleanRecord._modified;
                    delete cleanRecord._deleted;
                    operations.create.push(cleanRecord);
                } else if (record._modified || record.id) {
                    // Existing record - update
                    currentIds.push(record.id);
                    const cleanRecord = { ...record };
                    delete cleanRecord._tempId;
                    delete cleanRecord._isNew;
                    delete cleanRecord._modified;
                    delete cleanRecord._deleted;
                    operations.update.push(cleanRecord);
                }
            });
            
            // Find deleted records (in original but not in current)
            const deletedIds = originalIds.filter((id: number) => !currentIds.includes(id));
            operations.delete.push(...deletedIds);
            
            // Only include operations that have data
            const finalOperations: any = {};
            if (operations.create.length > 0) finalOperations.create = operations.create;
            if (operations.update.length > 0) finalOperations.update = operations.update;
            if (operations.delete.length > 0) finalOperations.delete = operations.delete;
            
            // Store formatted operations in payload
            if (Object.keys(finalOperations).length > 0) {
                payload[fieldName] = finalOperations;
            } else {
                // No changes, remove the field to avoid sending empty data
                delete payload[fieldName];
            }
        } else if ((fieldMeta as any)['type'] === 'many2many') {
            const currentIds = data[fieldName] || [];
            if (!Array.isArray(currentIds)) continue;
            
            const originalIds = originalData.value?.[fieldName] || [];
            
            // Calculate add and remove operations
            const addIds = currentIds.filter((id: number) => !originalIds.includes(id));
            const removeIds = originalIds.filter((id: number) => !currentIds.includes(id));
            
            const operations: any = {};
            if (addIds.length > 0) operations.add = addIds;
            if (removeIds.length > 0) operations.remove = removeIds;
            
            // Store formatted operations in payload
            if (Object.keys(operations).length > 0) {
                payload[fieldName] = operations;
            } else {
                // No changes, remove the field
                delete payload[fieldName];
            }
        }
    }
    return payload;
};

const onBtnAction = async (btn: any) => {
    // Handle reset password action specially
    if (btn.name === 'reset_password') {
        resetPasswordUserId.value = props.formData.id;
        resetPasswordUserName.value = props.formData.full_name || 'Unknown User';
        resetPasswordUserEmail.value = props.formData.email || 'Unknown Email';
        showResetPasswordModal.value = true;
        return;
    }
    
    // Handle other actions normally
    if (isDirty.value) {
        handleSave(() => {
            emit('action', btn);
        });
    } else {
        emit('action', btn);
    }
};

const closeResetPasswordModal = () => {
    showResetPasswordModal.value = false;
    resetPasswordUserId.value = 0;
    resetPasswordUserName.value = '';
    resetPasswordUserEmail.value = '';
};

const handleResetPasswordSuccess = () => {
    // Optionally refresh the form data or show additional feedback
    emit('refresh');
};

const handleDiscard = () => {
    if (!props.formData.id) {
        emit('cancel');
        return;
    }
    if (originalData.value) {
        Object.keys(originalData.value).forEach(key => {
            const field = allFields.value[key];
            
            if (field?.type === 'one2many') {
                // Special handling for one2many fields
                const originalArray = originalData.value[key];
                if (Array.isArray(originalArray)) {
                    // Deep clone the original array and clean up temp flags
                    props.formData[key] = originalArray.map(record => {
                        const cleanRecord = { ...record };
                        // Remove modification flags when discarding
                        delete cleanRecord._modified;
                        delete cleanRecord._tempId;
                        return cleanRecord;
                    });
                } else {
                    props.formData[key] = originalArray;
                }
            } else {
                // Regular field handling
                props.formData[key] = originalData.value[key];
            }
        });
    }
    showValidationErrors.value = false;
};

const relations = reactive<any>({});
const activeTab = ref('');

watch(viewDefinition, (val) => {
    if (val?.tabs?.length) activeTab.value = val.tabs[0].title;
}, { immediate: true });

watch(reactiveFormData, () => {
    const tabs = viewDefinition.value?.tabs;
    if (!tabs?.length) return;
    const current = tabs.find((tab: any) => tab.title === activeTab.value);
    if (current?.invisible && evaluateDomain(current.invisible, false)) {
        const firstVisible = tabs.find((tab: any) => !tab.invisible || !evaluateDomain(tab.invisible, false));
        if (firstVisible) activeTab.value = firstVisible.title;
    }
}, { deep: true });

const getNameField = () => props.metadata?.rec_name || 'name';
const getStatusField = () => props.metadata?.status_field || '';

const headerFields = computed(() => {
    const groups = viewDefinition.value.groups || [];
    return groups
        .filter((g: any) => g.position === 'header')
        .flatMap((g: any) => g.fields || []);
});

const nameFieldKey = computed(() => getNameField());

// New computed properties for right sidebar support
const hasRightSidebarGroups = computed(() => {
    return viewDefinition.value.groups?.some((group: any) => group.position === 'right') || false;
});

const getMainGroups = () => {
    return viewDefinition.value.groups?.filter((group: any) => group.position !== 'right' && group.position !== 'header') || [];
};

const getRightSidebarGroups = () => {
    return viewDefinition.value.groups?.filter((group: any) => group.position === 'right') || [];
};

const isTabInvalid = (tab: any) => {
    if (!showValidationErrors.value) return false;
    
    // Collect all fields in the tab (either directly or via groups)
    const allTabFields: string[] = [];
    if (tab.fields) {
        allTabFields.push(...tab.fields);
    }
    if (tab.groups) {
        tab.groups.forEach((g: any) => {
            if (g.fields) {
                allTabFields.push(...g.fields);
            }
        });
    }

    const hasInvalidFields = allTabFields.some((key: string) => {
        const field = allFields.value[key];
        if (!field) return false;
        
        // Check regular required fields
        if (isFieldRequired(key) && isFieldEmpty(props.formData[key])) {
            return true;
        }
        
        // Check one2many field validation
        if (field.type === 'one2many') {
            const fieldRef = one2manyFieldRefs.value.get(key);
            if (fieldRef && typeof fieldRef.validate === 'function') {
                const isValid = fieldRef.validate();
                if (!isValid) {
                    return true;
                }
            }
        }
        
        // Check many2many field validation
        if (field.type === 'many2many') {
            const fieldRef = many2manyFieldRefs.value.get(key);
            if (fieldRef && typeof fieldRef.validate === 'function') {
                const isValid = fieldRef.validate();
                if (!isValid) {
                    return true;
                }
            }
        }
        
        return false;
    });
    
    return hasInvalidFields;
};

const getStatusOptions = () => {
    const statusField = getStatusField();
    const field = allFields.value[statusField];
    if (!field) return [];

    if (field.type === 'many2one') {
        const rel = relations[statusField] || relations[field.relation] || [];
        return [...rel]
            .sort((a: any, b: any) => {
                const aSeq = typeof a?.sequence === 'number' ? a.sequence : Number.MAX_SAFE_INTEGER;
                const bSeq = typeof b?.sequence === 'number' ? b.sequence : Number.MAX_SAFE_INTEGER;
                if (aSeq !== bSeq) return aSeq - bSeq;
                return (a?.id || 0) - (b?.id || 0);
            })
            .map((record: any) => ({
                val: record.id,
                label: record.display_name || record.name || `#${record.id}`
            }));
    }
    
    // Handle both array and object formats for selection options
    if (Array.isArray(field.selection)) {
        return field.selection.map(([val, label]: any) => ({ val, label }));
    }
    if (field.options && typeof field.options === 'object') {
        return Object.entries(field.options).map(([val, opt]: any) => ({ val, label: opt.label || opt }));
    }
    return [];
};

const getOptions = (field: any, fieldName?: string) => {
    if (!field) return [];
    if (field.type === 'selection') {
        // Handle array format (selection field)
        if (field.selection && Array.isArray(field.selection)) {
            return field.selection.map(([val, label]: any) => ({ val, label }));
        }
        // Handle object format (options field)
        if (field.options && typeof field.options === 'object') {
            return Object.entries(field.options).map(([val, opt]: any) => ({ val, label: opt.label || opt }));
        }
        return [];
    }
    if (field.type === 'many2one') {
        // Check for field-specific options (for dynamic domains)
        if (fieldName && relations[fieldName]) {
             return (relations[fieldName] || []).map((r: any) => ({ 
                val: r.id, 
                label: r.display_name || r.name || r.full_name || r.subject || `#${r.id}` 
            }));
        }
        return (relations[field.relation] || []).map((r: any) => ({ 
            val: r.id, 
            label: r.display_name || r.name || r.full_name || r.subject || `#${r.id}` 
        }));
    }
    return [];
};

const getEditComponent = (field: any) => {
    if (!field) return 'input';
    if (field.type === 'text') return 'textarea';
    return 'input';
};

const getEditProps = (field: any) => {
    if (!field) return { class: 'form-control' };
    const p: any = { class: 'form-control' };
    if (field.type === 'date') p.type = 'date';
    if (field.type === 'email') p.type = 'email';
    if (field.type === 'float' || field.type === 'integer') {
        p.type = 'number';
        if (field.type === 'float') {
            p.step = '0.01';
        } else {
            p.step = '1';
        }
    }
    return p;
};

const handleRelationFocus = async (modelName: string, fieldName?: string) => {
    let relationKey = modelName;
    let params: any = {
        parent_model: props.modelName,
        limit: 500
    };
    let isDynamic = false;
    
    if (fieldName) {
         const field = allFields.value[fieldName];
         if (field && field.domain) {
              try {
                  const engine = new DomainEngine();
                  const domain = engine.resolveDomain(field.domain, props.formData);
                  if (domain.length) {
                      params.domain = JSON.stringify(domain);
                      relationKey = fieldName;
                      isDynamic = true;
                  }
              } catch(e) { 
                  // Silently handle domain resolution errors
              }
         }
    }

    if (isDynamic || !relations[relationKey]) {
        try {
            const resp = await api.get(`/models/${modelName}`, { params });
            // Backend now returns { items: [], total: number }
            relations[relationKey] = resp.data?.items || (Array.isArray(resp.data) ? resp.data : []);
        } catch (e) {
            // Relational fetch error - silently fail
        }
    }
};

onMounted(() => {
    Object.entries(allFields.value).forEach(([key, f]: any) => {
        if (f.type === 'many2one') handleRelationFocus(f.relation, key);
    });
    autoResizeTitle();
    
    // Close smart buttons dropdown when clicking outside
    const handleClickOutside = (e: MouseEvent) => {
        if (!e.target || !(e.target as Element).closest('.mobile-smart-dropdown, .mobile-action-btn')) {
            showSmartButtons.value = false;
        }
    };
    document.addEventListener('click', handleClickOutside);
    
    return () => {
        document.removeEventListener('click', handleClickOutside);
    };
});

watch(() => props.formData[getNameField()], () => {
  nextTick(() => {
    autoResizeTitle();
  });
});

// Watch specifically for status field changes (dynamic)
watch(() => props.formData?.[getStatusField()], (newStatus, oldStatus) => {
  if (newStatus !== undefined && getStatusField()) {
    nextTick(() => {
      forceLocalEvaluation();
    });
  }
});

// Watch for any reactive form data changes to trigger domain re-evaluation
watch(reactiveFormData, (newData, oldData) => {
  if (newData && oldData) {
    // Check if any field values have changed
    const changedFields = Object.keys(newData).filter(key => 
      newData[key] !== oldData[key]
    );
    
    if (changedFields.length > 0) {
      // Force local domain evaluation for real-time updates
      nextTick(() => {
        forceLocalEvaluation();
      });
    }
  }
}, { deep: true });

// Also watch props.formData for external changes
watch(() => props.formData, (newData, oldData) => {
  if (newData && oldData) {
    // Check if any field values have changed
    const changedFields = Object.keys(newData).filter(key => 
      newData[key] !== oldData[key]
    );
    
    if (changedFields.length > 0) {
      // Force local domain evaluation for real-time updates
      nextTick(() => {
        forceLocalEvaluation();
      });
    }
  }
}, { deep: true });

// Watch for changes in formData.id to refresh permissions
watch(() => props.formData?.id, (newId, oldId) => {
  if (newId !== oldId) {
    refreshPermissions();
    // Refresh audit log when record ID changes (after save)
    if (auditLogRef.value && newId) {
      nextTick(() => {
        (auditLogRef.value as any)?.refresh?.();
      });
    }
  }
}, { immediate: true });

// Watch for saving prop to refresh audit log after save completes
watch(() => props.saving, (isSaving, wasSaving) => {
  if (wasSaving && !isSaving && props.formData?.id && auditLogRef.value) {
    // Save just completed, refresh audit log
    nextTick(() => {
      (auditLogRef.value as any)?.refresh?.();
    });
  }
});

watch(allFields, (val) => {
    Object.values(val).forEach((f: any) => {
        if (f.type === 'many2one') handleRelationFocus(f.relation);
    });
});

defineExpose({
    isDirty
});
</script>

<style lang="scss" scoped>
@use "../../styles/variables" as v;

.base-form-pivot {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: v.$bg-main;
  min-height: 0;
  position: relative;
  overflow: hidden;
}

/* --- Znova-Style Mobile Header --- */
.mobile-header-znova {
  flex: 0 0 auto;
  background: v.$white;
  border-bottom: 1px solid v.$border-color;
  z-index: 30;
}

.mobile-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  height: 56px;
}

.mobile-left-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
  min-width: 0;
  
  .page-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: v.$text-primary;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.mobile-back-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: v.$text-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: v.$radius-btn;
  min-width: 44px;
  min-height: 44px;
  flex-shrink: 0;
  
  &:hover {
    background: v.$bg-main;
  }
}

.mobile-title-center {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  
  .page-title {
    font-size: 1.125rem;
    font-weight: 600;
    color: v.$text-primary;
    white-space: nowrap;
  }
}

.mobile-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
}

.mobile-action-btn {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: v.$text-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: v.$radius-btn;
  min-width: 44px;
  min-height: 44px;
  
  &:hover {
    background: v.$bg-main;
  }
  
  &:disabled {
    color: v.$text-disabled;
    cursor: not-allowed;
  }
}

.mobile-pager-btns {
  display: flex;
  gap: 1px;
  background: v.$border-color;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-btn;
  overflow: hidden;
}

.mobile-btn-pager {
  background: v.$white;
  border: none;
  padding: 0.4rem;
  display: flex;
  align-items: center;
  cursor: pointer;
  color: v.$text-primary;
  
  &:disabled {
    color: v.$text-disabled;
    cursor: not-allowed;
  }
  
  &:not(:disabled):hover {
    background: v.$bg-main;
  }
}

.mobile-smart-dropdown {
  background: v.$bg-main;
  border-bottom: 1px solid v.$border-color;
  animation: slideDown 0.2s ease-out;
  
  .dropdown-section {
    &:not(:first-child) {
      border-top: 1px solid v.$border-color;
    }
  }
  
  .section-header {
    padding: 0.5rem 1rem;
    font-size: 0.75rem;
    font-weight: 700;
    color: v.$text-secondary;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    background: rgba(v.$border-color, 0.3);
  }
  
  .smart-button-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    cursor: pointer;
    color: v.$text-primary;
    transition: background 0.15s;
    
    &:hover {
      background: v.$white;
    }
    
    .icon-sm {
      color: v.$primary-color;
    }
  }
}

.mobile-action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: v.$bg-main;
  border-bottom: 1px solid v.$border-color;
  gap: 1rem;
}

.mobile-save-actions {
  display: flex;
  gap: 0.5rem;
  flex: 1;
}

.mobile-empty-space {
  flex: 1;
}

.mobile-header-actions {
  display: flex;
  margin-left: 0.5rem;
}

.mobile-action-btn-small {
  padding: 0.5rem 1rem;
  height: 36px;
  font-size: 0.875rem;
  flex: 1;
  min-width: 80px;
}

.mobile-pagination-info {
  .page-info {
    font-size: 0.875rem;
    color: v.$text-secondary;
    font-weight: 500;
    white-space: nowrap;
  }
}

@keyframes slideDown {
  from { 
    opacity: 0;
    transform: translateY(-10px); 
  }
  to { 
    opacity: 1;
    transform: translateY(0); 
  }
}

/* --- Desktop Action Bar --- */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  margin: 24px 24px 0 24px; // Added margin to match List
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: 16px; // radius-lg
  flex-shrink: 0;
  gap: 24px;
  box-shadow: v.$shadow-sm;
  z-index: 20;
}

// Dark mode action bar
[data-theme="dark"] .action-bar {
  background: #161b22;
  border-color: #30363d;
}

.action-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.action-bar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Pager & Arrows (Shared with List style) */
.pager-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-arrows {
  display: flex;
  gap: 2px;
  background: v.$bg-main;
  padding: 4px;
  border-radius: v.$radius-btn;
  border: 1px solid v.$border-color;
}

// Dark mode nav arrows
[data-theme="dark"] .nav-arrows {
  background: #0d1117;
  border-color: #30363d;
}

.nav-arrow {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: v.$text-secondary;
  cursor: pointer;
  border-radius: v.$radius-btn;
  transition: all 0.2s;

  &:hover:not(:disabled) {
    background: v.$white;
    color: v.$text-primary;
    box-shadow: v.$shadow-sm;
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

// Dark mode nav arrow
[data-theme="dark"] .nav-arrow {
  color: #7d8590;
  
  &:hover:not(:disabled) {
    background: #161b22;
    color: #e6edf3;
  }
}

.pager-info {
  font-size: 14px;
  color: v.$text-secondary;
  font-weight: 500;
  padding: 0 4px;
  min-width: 70px;
  text-align: center;
}

// Dark mode pager info
[data-theme="dark"] .pager-info {
  color: #7d8590;
}

.actions-dropdown-container {
  position: relative;
  display: flex;
  align-items: center;
}

.action-trigger {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  font-weight: 500;
  height: 36px; /* Match standard button height */
  
  @media (max-width: 768px) {
    padding: 0.4rem 0.6rem;
    font-size: 0.8125rem;
    height: 32px;
  }
}

.action-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-lg;
  box-shadow: 0 10px 15px -3px v.$shadow-color-md, 0 4px 6px -2px v.$shadow-color-sm;
  z-index: 1000;
  min-width: 160px;
  overflow: hidden;
  animation: slideInDown 0.15s ease-out;
}

.action-menu-mobile {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: v.$white;
  border: 1px solid v.$border-color;
  border-radius: v.$radius-lg;
  box-shadow: 0 4px 6px -1px v.$shadow-light;
  z-index: 1000;
  min-width: 140px;
  overflow: hidden;
}

.mobile-actions-inline {
  display: flex;
  margin-left: 0.5rem;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  cursor: pointer;
  font-size: 0.875rem;
  color: v.$text-primary;
  transition: background 0.15s;
  
  &:hover {
    background: v.$bg-main;
  }
  
  &.danger {
    color: v.$danger-color;
    
    &:hover {
      background: #FEF2F2;
    }
  }

  &.group-danger {
    &:hover {
      background: #FEF2F2 !important;
    }
  }
}

[data-theme="dark"] .action-button {
  &.danger:hover {
    background: rgba(248, 81, 73, 0.1);
  }
  
  &.group-danger:hover {
    background: rgba(248, 81, 73, 0.1) !important;
  }
}

@keyframes slideInDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.action-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: transparent;
}

.record-pager {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  
  .pager-info { font-size: 0.8125rem; color: v.$text-secondary; font-weight: 500; }
  .pager-btns {
    display: flex;
    gap: 1px;
    background: v.$border-color;
    border: 1px solid v.$border-color;
    border-radius: v.$radius-btn;
    overflow: hidden;
  }
}

.btn-pager {
  background: v.$white; border: none; padding: 0.4rem; display: flex; align-items: center; cursor: pointer;
  color: v.$text-primary;
  &:disabled { color: v.$text-disabled; cursor: not-allowed; }
  &:not(:disabled):hover { background: v.$bg-main; }
}

.status-bar-integrated {
  flex: 0 0 auto;
  padding: 0.75rem 0;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 1.5rem;

  @media (max-width: 767px) {
    display: none; /* Hide on mobile since actions are in the menu */
  }
}

.status-left { display: flex; gap: 0.5rem; justify-content: flex-start; align-items: center; }
.action-buttons { display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center; }
.status-center { display: flex; justify-content: center; align-items: center; }
.status-right { display: flex; justify-content: flex-end; align-items: center; }

.status-pipeline {
  display: flex;
  background: v.$border-light;
  // Removed global radius and overflow to target children specifically
  
  .status-step {
    padding: 0 1.25rem;
    height: 36px;
    display: flex;
    align-items: center;
    font-size: 0.75rem;
    font-weight: 700;
    color: v.$text-placeholder;
    text-transform: uppercase;
    border-right: 1px solid v.$white;
    transition: all 0.2s;

    &:first-child {
      border-top-left-radius: v.$radius-lg;
      border-bottom-left-radius: v.$radius-lg;
    }

    &:last-child {
      border-top-right-radius: v.$radius-lg;
      border-bottom-right-radius: v.$radius-lg;
      border-right: none;
    }
    
    &.active {
      background: v.$primary-color;
      color: v.$white;
    }
  }
}

.sheet-viewport {
  flex: 1;
  display: flex;
  flex-direction: row;
  min-height: 0;
  overflow: hidden;
  /* Ensure dropdowns can extend beyond viewport bounds */
  position: relative;
}

.integrated-content-wrapper {
  width: 100%;
  display: flex;
  flex-direction: row;
  flex: 1;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
}

.form-main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
  padding: 0 1.5rem;
  
  @media (max-width: 1023px) {
    padding: 0 0.75rem;
  }
}

.form-content-scrollable {
  flex: 1;
  overflow-y: auto;
  overflow-x: visible;
  padding-bottom: 1.5rem;
  min-height: 0;
  max-height: 100%;
  
  /* Smooth scrolling */
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  
  /* Custom scrollbar styling */
  &::-webkit-scrollbar {
    width: 8px;
  }
  
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  
  &::-webkit-scrollbar-thumb {
    background: v.$border-color;
    border-radius: 4px;
    
    &:hover {
      background: v.$text-disabled;
    }
  }
  
  @media (max-width: 1023px) {
    padding-bottom: 0.75rem;
  }
}

// Dark mode form content scrollable
[data-theme="dark"] .form-content-scrollable {
  &::-webkit-scrollbar-thumb {
    background: #30363d;
    
    &:hover {
      background: #484f58;
    }
  }
}

.form-sheet-expanded {
  background: v.$white;
  padding: 1rem 2rem;
  border: 1px solid v.$border-color;
  box-shadow: 0 1px 3px v.$shadow-color-sm;
  border-radius: v.$radius-lg;
  /* Ensure dropdowns can extend beyond form sheet bounds */
  position: relative;
  overflow: visible;
  @media (max-width: 1023px) {
    padding: 1.5rem 1rem;
  }
}

// Dark mode form sheet
[data-theme="dark"] .form-sheet-expanded {
  background: #161b22;
  border-color: #30363d;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.sheet-header {
  padding: 0.75rem 0 1rem;
}

.header-main-title {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.5rem;
  min-height: 60px;
  padding: 0.75rem 0;
  
  @media (max-width: 1023px) {
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
    min-height: auto;
    gap: 1rem;
  }
}

.header-title-section {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch; /* Change to stretch to ensure full width */
  gap: 0.5rem;
  width: 100%;
  
  @media (max-width: 1023px) {
    width: 100%;
    order: 1;
  }
}

.header-priority-top {
  display: flex;
  align-items: center;
  margin-bottom: 0.25rem;
  
  @media (max-width: 1023px) {
    margin-bottom: 0.5rem;
  }
}

.header-title {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  width: 100%;
  
  @media (max-width: 1023px) {
    align-items: flex-start;
    text-align: left;
  }
}



.header-image {
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
  flex-shrink: 0;
  padding-top: 0.25rem;
  
  @media (max-width: 1023px) {
    margin-top: 0.5rem;
    justify-content: flex-start;
    order: 3;
    padding-top: 0;
  }
  
  // Override ImageField styles for header placement
  :deep(.image-field-container) {
    .image-preview,
    .image-placeholder {
      width: 50px;
      height: 50px;
      border-radius: 6px;
      box-shadow: 0 1px 4px v.$shadow-light;
      transition: all 0.2s ease;
    }
    
    .image-preview {
      border: 1px solid v.$border-light;
      
      &:hover {
        border-color: v.$primary-color;
        box-shadow: 0 2px 6px v.$shadow-medium;
      }
    }
    
    .image-placeholder {
      border: 1px dashed v.$border-color;
      background: v.$bg-main;
      
      &:hover {
        border-color: v.$primary-color;
        background: rgba(v.$primary-color, 0.05);
      }
      
      .placeholder-icon {
        width: 16px;
        height: 16px;
      }
      
      .placeholder-text {
        font-size: 0.6rem;
        font-weight: 500;
      }
    }
    
    .overlay-btn {
      min-width: 20px;
      min-height: 20px;
      padding: 0.15rem;
    }
    
    @media (max-width: 1023px) {
      .image-preview,
      .image-placeholder {
        width: 45px;
        height: 45px;
      }
      
      .placeholder-icon {
        width: 14px;
        height: 14px;
      }
      
      .placeholder-text {
        font-size: 0.55rem;
      }
    }
  }
}

.header-image-section {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  justify-content: flex-end;
  
  @media (max-width: 1023px) {
    justify-content: flex-start;
  }
}

.header-widget-wrapper {
  width: 100%;
  margin-top: 0.25rem;
}

.header-selection, .header-many2one, .header-date, .header-fallback {
  width: 100%;
  /* Removed max-width to allow full horizontal expansion */
  
  :deep(.form-control), :deep(.view-value) {
    font-size: 2rem !important;
    font-weight: 700 !important;
    height: auto !important;
    min-height: 48px !important;
    padding: 4px 0 !important;
    border-bottom-width: 3px !important;
  }
  
  :deep(.many2one-input-wrapper) {
     input {
        font-size: 2rem !important;
        font-weight: 700 !important;
        height: 48px !important;
     }
  }
}
.sheet-header .header-title {
    .model-label { font-size: 0.875rem; color: v.$text-secondary; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
    h1 { font-size: 3rem; margin: 0.25rem 0 0 0; font-weight: 800; color: v.$text-primary; letter-spacing: -0.02em; line-height: 1.2; word-break: break-word; }
    .title-display {
      font-size: 3rem; margin: 0.25rem 0 0 0; font-weight: 800; color: v.$text-primary; 
      letter-spacing: -0.02em; line-height: 1.2; word-break: break-word;
      
      @media (max-width: 1023px) {
        font-size: 2rem;
      }
    }
    .title-input {
      font-size: 3rem; width: 100%; border: none; background: transparent; 
      border-bottom: 2px solid transparent; outline: none; margin-top: 0.25rem;
      font-family: inherit; font-weight: 800; letter-spacing: -0.02em;
      line-height: 1.2; resize: none; overflow: hidden;
      transition: all 0.2s; text-align: left;
      margin-left: 0; padding: 0.25rem 0.5rem; border-radius: 4px;
      &:hover, &:focus { 
        border-bottom-color: v.$primary-color; 
        background: rgba(v.$primary-color, 0.02);
      }

      @media (max-width: 1023px) {
        font-size: 2rem;
      }
    }
  }

.sheet-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  
  &.single-column {
    grid-template-columns: 1fr;
  }
  
  &.has-right-sidebar {
    grid-template-columns: 1fr auto;
    gap: 2rem;
    
    .main-content {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1.5rem;
    }
  }
  
  &.mobile-layout {
    grid-template-columns: 1fr;
    gap: 1.5rem;
    
    &.has-right-sidebar {
      grid-template-columns: 1fr;
      
      .main-content {
        grid-template-columns: 1fr;
      }
      
      .right-sidebar {
        margin-top: 1.5rem;
      }
    }
  }
  
  &.tablet-layout {
    grid-template-columns: 1fr;
    gap: 2rem;
    
    &.has-right-sidebar {
      grid-template-columns: 1fr;
      
      .main-content {
        grid-template-columns: 1fr;
      }
      
      .right-sidebar {
        margin-top: 2rem;
      }
    }
  }
  
  @media (max-width: 1023px) {
    grid-template-columns: 1fr;
    gap: 1.5rem;
    
    &.has-right-sidebar {
      .main-content {
        grid-template-columns: 1fr;
      }
      
      .right-sidebar {
        margin-top: 1.5rem;
      }
    }
  }
}

.group-title {
  font-size: 1rem; font-weight: 800; color: v.$text-primary;
  border-bottom: 2px solid v.$border-light;
  padding-bottom: 0.5rem; margin-bottom: 1.25rem;
}

.grid-column { 
  display: flex; 
  flex-direction: column; 
  gap: 0.75rem; 
}

.right-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  min-width: 250px;
  max-width: 350px;
}

.sidebar-group {
  background: v.$bg-main;
  border: 1px solid v.$border-light;
  border-radius: v.$radius-lg;
  padding: 1.5rem;
  
  .group-title {
    font-size: 0.875rem;
    font-weight: 600;
    color: v.$text-secondary;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid v.$border-light;
    padding-bottom: 0.5rem;
    margin-bottom: 1rem;
  }
}

.sidebar-field-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.field-item {
  display: grid;
  grid-template-columns: 160px 1fr;
  align-items: center;
  min-height: 40px;

  &.mobile-field {
    grid-template-columns: 1fr;
    gap: 0.25rem;
    align-items: flex-start;
    min-height: 44px; // Touch-friendly minimum
  }

  @media (max-width: 1023px) {
    grid-template-columns: 1fr;
    gap: 0.25rem;
    align-items: flex-start;
  }

  &.no-label {
    grid-template-columns: 1fr;
    
    .field-wrapper {
        grid-column: 1 / -1;
    }
  }
  
  &.full-width-field {
    grid-template-columns: 1fr;
    gap: 0.5rem;
    align-items: flex-start;
    
    label {
      margin-bottom: 0.5rem;
    }
    
    .field-wrapper {
      width: 100%;
    }
  }
  
  label { 
    font-size: 0.875rem; 
    font-weight: 600; 
    color: v.$text-secondary; 
    
    &.required-label {
      &::after {
        content: ' *';
        color: v.$danger-color;
        font-weight: 700;
      }
    }
  }
  
  .field-wrapper {
    position: relative; 
    display: flex;
    align-items: center;
    min-height: 32px;
    width: 100%;
    max-width: 100%;
  }
  
  .view-value { font-size: 1rem; color: v.$text-primary; font-weight: 500; white-space: pre-wrap; }
}

.form-control {
    width: 100%; border: none; background: transparent; outline: none;
    font-size: 1rem; color: v.$text-primary; font-weight: 500;
    border-bottom: 1px solid transparent;
    transition: all 0.2s;
    border-radius: 0;
    font-family: inherit;
    height: 32px;
    
    // Reset browser defaults for select
    appearance: none;
    -webkit-appearance: none;
    
    &:hover { 
      border-bottom-color: v.$border-color; 
    }

    &:focus {
      border-bottom-color: v.$primary-color !important;
      border-bottom-width: 2px;
      margin-bottom: -1px;
    }
    
    &[type="date"] { cursor: pointer; }
    
    // Add custom arrow for select
    &.select-custom {
      background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
      background-repeat: no-repeat;
      background-position: right 0 center;
      background-size: 1.25rem;
      padding-right: 1.5rem;
    }
}

// Field validation styles
.field-invalid {
  border-bottom-color: v.$danger-color !important;
  color: v.$danger-color !important;
  
  &:hover {
    border-bottom-color: v.$danger-color !important;
  }
  
  &:focus {
    border-bottom-color: v.$danger-color !important;
  }
}

.form-text-area.field-invalid {
  border: 1px solid v.$danger-color !important;
  color: v.$danger-color !important;
}

.title-input.field-invalid {
  border-bottom-color: v.$danger-color !important;
  color: v.$danger-color !important;
}

.sheet-tabs {
  margin-top: 1rem;
  min-width: 0; // Allow shrinking in flex container
  overflow: hidden; // Prevent overflow from breaking layout
  
  .tab-content {
    overflow-x: auto;
    min-width: 0;
    max-width: 100%;
  }
  
  .tab-pane {
    width: 100%;
    
    // Make fields in tabs without groups full-width
    > .field-item {
      max-width: 100%;
    }
  }
  
  .tabs-header {
    display: flex; border-bottom: 1px solid v.$border-color; margin-bottom: 1.5rem;
    -webkit-overflow-scrolling: touch;
    
    &.mobile-tabs {
      overflow-x: auto;
      scrollbar-width: none; // Firefox
      -ms-overflow-style: none; // IE/Edge
      &::-webkit-scrollbar {
        display: none; // Chrome/Safari
      }
    }
    
    .tab-item {
      padding: 0.8rem 2rem; cursor: pointer; color: v.$text-placeholder; font-weight: 800;
      border-bottom: 3.5px solid transparent; margin-bottom: -2.5px; font-size: 0.875rem;
      text-transform: uppercase; letter-spacing: 0.05em;
      white-space: nowrap;
      
      @media (max-width: 1023px) {
        padding: 0.8rem 1.25rem;
        min-width: 120px; // Ensure touch-friendly width
        text-align: center;
      }

      &.active { border-color: v.$primary-color; color: v.$primary-color; }
      &:hover:not(.active) { color: v.$text-secondary; }
    }
  }
}

.full-field-text {
  grid-column: span 2;
  margin-top: 1rem;
  
  label { 
     font-size: 0.875rem; font-weight: 700; margin-bottom: 1.25rem; 
     display: block; color: v.$text-secondary; 
  }
}

.form-text-area {
    width: 100%; border: none; padding: 0.5rem 0; 
    border-bottom: 1px solid transparent;
    outline: none; font-family: inherit; font-size: 1rem; line-height: 1.7;
    background: transparent;
    transition: all 0.2s;
    resize: vertical;
    
    &:hover { 
      border-bottom-color: v.$border-color;
    }
    
    &:focus { 
      border-bottom-color: v.$primary-color;
      border-bottom-width: 2px;
      margin-bottom: -1px;
    }
}

.btn {
  padding: 0 1.5rem; height: 36px; border-radius: v.$radius-btn; font-weight: 500; font-size: 0.875rem;
  cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
  transition: all 0.2s; border: 1px solid transparent; gap: 0.5rem;
}
.btn-sm { padding: 0 1rem; height: 32px; font-size: 0.8125rem; }
.btn-primary { background: v.$primary-color; color: v.$white; &:hover { background: v.$primary-hover; } }
.btn-secondary { background: v.$white; border-color: v.$border-color; color: v.$text-primary; &:hover { background: v.$bg-main; border-color: v.$text-disabled; } }
.btn-danger { background: v.$danger-color; color: v.$white; &:hover { background: v.$red-600; } }

// Dark mode buttons
[data-theme="dark"] {
  .btn-primary {
    background: #2563eb;
    
    &:hover {
      background: #1d4ed8;
    }
  }
  
  .btn-secondary {
    background: #161b22;
    border-color: #30363d;
    color: #e6edf3;
    
    &:hover {
      background: #0d1117;
      border-color: #7d8590;
    }
  }
  
  .btn-danger {
    background: #f85149;
    
    &:hover {
      background: #da3633;
    }
  }
}

.icon-sm { width: 16px; height: 16px; }

.required-label::after {
  content: " *";
  color: v.$danger-color;
  font-weight: bold;
}

.field-invalid {
  border-bottom: 1px solid v.$danger-color !important;
  background: transparent !important;
}

.field-readonly {
  background-color: v.$bg-main !important;
  color: v.$text-secondary !important;
  cursor: not-allowed !important;
  
  &:hover {
    border-bottom-color: transparent !important;
  }
  
  &:focus {
    border-bottom-color: transparent !important;
    border-bottom-width: 1px !important;
    margin-bottom: 0 !important;
  }
}

.invalid-tab {
  color: v.$danger-color !important;
  border-color: v.$danger-color !important;
}
</style>
