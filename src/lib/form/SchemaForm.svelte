<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import type { JSONSchema } from "json-schema-to-typescript";
  import CheckboxArray from "$lib/form/components/CheckboxArray.svelte";
  import ImageCheckboxArray from "$lib/form/components/ImageCheckboxArray.svelte";
  import AlnumGroupedCheckboxArray from "$lib/form/components/AlnumGroupedCheckboxArray.svelte";
  import TaskList from "$lib/form/components/TaskList.svelte";
  import type { SettingsProps } from "$lib/menu/model";
  import StringArray from "$lib/form/components/StringArray.svelte";
  import { asArraySchema, asNonEmptyStringArray } from "$lib/form/types";

  let {
    settingsProps = $bindable(),
  }: {
    settingsProps: SettingsProps;
  } = $props();

  interface Section {
    key: string;
    schema: JSONSchema;
  }

  let sections: Section[] = $derived.by(() => {
    return Object.entries(settingsProps.formSchema.properties ?? {})
      .map(([key, value]) => {
        if (!("$ref" in value)) return null;

        const defName = value.$ref?.replace("#/$defs/", "");
        if (!defName) return null;

        const sectionSchema = settingsProps.formSchema.$defs?.[defName];
        if (!sectionSchema) return null;

        const resolvedProps: Record<string, any> = {};
        Object.entries(sectionSchema.properties ?? {}).forEach(
          ([propKey, prop]) => {
            if (propKey === "theme") return;
            resolvedProps[propKey] = resolveRef(prop, settingsProps.formSchema);
          },
        );

        if (Object.keys(resolvedProps).length === 0) return null;

        return {
          key,
          schema: {
            ...sectionSchema,
            title: value.title ?? sectionSchema.title,
            properties: resolvedProps,
          },
        };
      })
      .filter(Boolean) as Section[];
  });

  function resolveRef(prop: any, rootSchema: JSONSchema) {
    if ("$ref" in prop && typeof prop.$ref === "string") {
      const refName = prop.$ref.replace("#/$defs/", "");
      return rootSchema.$defs?.[refName] ?? prop;
    }

    if (prop.type === "array" && prop.items?.$ref) {
      const refName = prop.items.$ref.replace("#/$defs/", "");
      return {
        ...prop,
        items: rootSchema.$defs?.[refName] ?? prop.items,
      };
    }

    return prop;
  }

  let activeSectionKey = $state<string>("");

  $effect(() => {
    // Auto-select the first section when sections change
    if (
      sections.length > 0 &&
      !sections.find((s) => s.key === activeSectionKey)
    ) {
      activeSectionKey = sections[0].key;
    }
  });

  const activeSection = $derived(
    sections.find((s) => s.key === activeSectionKey) ?? sections[0],
  );
</script>

<form id="schema-form" class="schema-form" onsubmit={(e) => e.preventDefault()}>
  {#if sections.length > 1}
    <div class="tab-bar" role="tablist">
      {#each sections as section}
        <button
          type="button"
          role="tab"
          aria-selected={activeSectionKey === section.key}
          class="tab"
          class:active={activeSectionKey === section.key}
          onclick={() => (activeSectionKey = section.key)}
        >
          {$t(section.schema.title ?? section.key)}
        </button>
      {/each}
    </div>
  {/if}

  {#if activeSection}
    {@const { key, schema } = activeSection}
    <div class="section-content">
      {#each Object.entries(schema.properties ?? {}) as [propKey, prop]}
        {@const arraySchema = asArraySchema(prop)}
        {@const choices = asNonEmptyStringArray(prop)}

        <div class="field">
          {#if arraySchema && arraySchema.items.enum && Array.isArray(settingsProps.formData[key]?.[propKey]) && choices}
            {#if prop.formType === "TaskList"}
              <div class="field-label">{$t(arraySchema.title ?? propKey)}</div>
              <TaskList
                {choices}
                bind:value={settingsProps.formData[key][propKey] as any}
              />
            {:else if prop.formType === "AlnumGroupedCheckboxArray"}
              <AlnumGroupedCheckboxArray
                title={$t(arraySchema.title ?? propKey)}
                {choices}
                bind:value={settingsProps.formData[key][propKey] as any}
              />
            {:else}
              <div class="field-label">{$t(arraySchema.title ?? propKey)}</div>
              {#if arraySchema.formType === "ImageCheckboxArray"}
                <ImageCheckboxArray
                  {choices}
                  assetPath={arraySchema.assetPath as string}
                  bind:value={settingsProps.formData[key][propKey] as any}
                />
              {:else}
                <CheckboxArray
                  {choices}
                  bind:value={settingsProps.formData[key][propKey] as any}
                />
              {/if}
            {/if}
          {:else if arraySchema && arraySchema.items.type === "string" && Array.isArray(settingsProps.formData[key]?.[propKey])}
            <div class="field-label">{$t(arraySchema.title ?? propKey)}</div>
            <StringArray
              bind:value={settingsProps.formData[key][propKey] as any}
              minItems={arraySchema.minItems}
            />
          {:else if prop.type === "boolean"}
            <!-- Boolean: inline label + toggle on right -->
            <label class="field-toggle" for={`${key}-${propKey}`}>
              <span class="field-toggle-text">
                <span class="field-label-inline">
                  {$t(prop.title ?? propKey)}
                </span>
                {#if prop.description}
                  <span class="field-hint">{$t(prop.description)}</span>
                {/if}
              </span>
              <span class="toggle-switch">
                <input
                  id={`${key}-${propKey}`}
                  type="checkbox"
                  bind:checked={
                    () => Boolean(settingsProps.formData[key]?.[propKey]),
                    (v) => (settingsProps.formData[key][propKey] = v)
                  }
                />
                <span class="slider"></span>
              </span>
            </label>
          {:else}
            <label class="field-label" for={`${key}-${propKey}`}>
              {$t(prop.title ?? propKey)}
            </label>
            {#if prop.description}
              <div class="field-hint">{$t(prop.description)}</div>
            {/if}
            {#if prop.enum}
              <select
                id={`${key}-${propKey}`}
                class="control select"
                bind:value={settingsProps.formData[key][propKey]}
              >
                {#each prop.enum as option}
                  <option value={option}>{$t(String(option))}</option>
                {/each}
              </select>
            {:else if prop.type === "integer" || prop.type === "number"}
              {#if prop.formType === "slider"}
                <div class="slider-container">
                  <input
                    id={`${key}-${propKey}`}
                    type="range"
                    class="range-input"
                    min={prop.minimum}
                    max={prop.maximum}
                    step={prop.multipleOf ??
                      (prop.type === "integer" ? 1 : 0.1)}
                    bind:value={settingsProps.formData[key][propKey]}
                  />
                  <span class="range-value"
                    >{settingsProps.formData[key][propKey]}</span
                  >
                </div>
              {:else}
                <input
                  id={`${key}-${propKey}`}
                  type="number"
                  class="control"
                  min={prop.minimum}
                  max={prop.maximum}
                  step={prop.multipleOf ??
                    (prop.type === "integer" ? 1 : "any")}
                  bind:value={settingsProps.formData[key][propKey]}
                />
              {/if}
            {:else}
              <input
                id={`${key}-${propKey}`}
                type="text"
                class="control"
                bind:value={settingsProps.formData[key][propKey]}
                {...prop.regex ? { pattern: prop.regex } : {}}
                {...prop.htmlTitle ? { title: prop.htmlTitle } : {}}
              />
            {/if}
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</form>

<style>
  .schema-form {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--bg-1);
  }

  .tab-bar {
    display: flex;
    gap: 2px;
    padding: 8px 16px 0;
    border-bottom: 1px solid var(--line);
    overflow-x: auto;
  }

  .tab {
    padding: 8px 14px;
    border: 0;
    background: transparent;
    color: var(--text-3);
    font-size: 12.5px;
    font-weight: 600;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition:
      color var(--dur-1),
      border-color var(--dur-1);
    white-space: nowrap;
    cursor: pointer;
  }

  .tab:hover {
    color: var(--text-1);
  }

  .tab.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
  }

  .section-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field-label {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-1);
  }

  .field-hint {
    font-size: 11.5px;
    color: var(--text-3);
    line-height: 1.4;
  }

  .control {
    width: 100%;
    padding: 8px 10px;
    border-radius: 8px;
    background: var(--bg-2);
    border: 1px solid var(--line);
    color: var(--text-1);
    font-size: 13px;
    font-family: inherit;
    transition:
      border-color var(--dur-1),
      box-shadow var(--dur-1);
  }

  .control:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-ring);
  }

  .select {
    appearance: none;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23a3a3a3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='m6 9 6 6 6-6'/></svg>");
    background-repeat: no-repeat;
    background-position: right 10px center;
    padding-right: 30px;
  }

  .select option {
    background-color: var(--bg-1);
    color: var(--text-1);
  }

  /* Boolean field: inline row */
  .field-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 10px 0;
    cursor: pointer;
  }

  .field-toggle-text {
    display: flex;
    flex-direction: column;
    gap: 3px;
    flex: 1;
    min-width: 0;
  }

  .field-label-inline {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-1);
  }

  .toggle-switch {
    position: relative;
    display: inline-block;
    width: 36px;
    height: 20px;
    flex-shrink: 0;
  }

  .toggle-switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: var(--bg-3);
    transition: 0.3s;
    border-radius: 20px;
    border: 1px solid var(--line);
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 14px;
    width: 14px;
    left: 2px;
    bottom: 2px;
    background-color: var(--text-2);
    transition: 0.3s;
    border-radius: 50%;
  }

  input:checked + .slider {
    background-color: var(--accent-ghost);
    border-color: var(--accent);
  }

  input:checked + .slider:before {
    transform: translateX(16px);
    background-color: var(--accent);
  }

  /* Range slider */
  .slider-container {
    display: flex;
    align-items: center;
    gap: 12px;
    width: 100%;
  }

  .range-input {
    flex: 1;
    appearance: none;
    height: 6px;
    border-radius: 3px;
    background: var(--bg-3);
    border: 1px solid var(--line);
    outline: none;
  }

  .range-input::-webkit-slider-thumb {
    appearance: none;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: var(--accent);
    cursor: pointer;
    border: 2px solid white;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    transition: transform 0.1s;
  }

  .range-input::-webkit-slider-thumb:hover {
    transform: scale(1.1);
  }

  .range-value {
    min-width: 40px;
    font-family: var(--font-mono);
    font-size: 12px;
    font-weight: 600;
    color: var(--text-1);
    text-align: right;
  }
</style>
