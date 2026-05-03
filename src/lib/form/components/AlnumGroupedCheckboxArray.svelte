<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import { updateCheckboxArray } from "$lib/form/checkboxHelper";
  import NoOptionsAvailable from "$lib/components/generic/NoOptionsAvailable.svelte";
  import type { AlnumGroupedCheckboxArrayProps } from "$lib/form/types";

  let {
    title,
    choices,
    value = $bindable(),
  }: AlnumGroupedCheckboxArrayProps = $props();

  let query = $state("");

  interface Option {
    original: string;
    translated: string;
  }

  // All options sorted by translated label
  const allOptions = $derived.by(() => {
    const opts: Option[] = (choices || []).map((c) => ({
      original: c,
      translated: $t(c),
    }));
    opts.sort((a, b) => a.translated.localeCompare(b.translated));
    return opts;
  });

  // Filtered by search query
  const filteredOptions = $derived(
    query.trim()
      ? allOptions.filter((o) =>
          o.translated.toLowerCase().includes(query.trim().toLowerCase()),
        )
      : allOptions,
  );

  // Group filtered options by first letter
  const groups = $derived.by(() => {
    const map = new Map<string, Option[]>();
    for (const opt of filteredOptions) {
      const letter = opt.translated.charAt(0).toUpperCase();
      if (!map.has(letter)) map.set(letter, []);
      map.get(letter)!.push(opt);
    }
    return [...map.entries()];
  });

  function toggle(original: string, checked: boolean) {
    value = updateCheckboxArray(value, original, checked);
  }

  function clearAll() {
    value = [];
  }

  function selectAll() {
    value = allOptions.map((o) => o.original);
  }

  const selectedCount = $derived(value?.length ?? 0);
  const totalCount = $derived(allOptions.length);
</script>

<div class="grouped-array">
  <div class="header">
    <div class="title-row">
      <span class="title">{$t(title)}</span>
      <span class="count">
        {selectedCount} / {totalCount}
      </span>
    </div>
    <div class="actions">
      {#if selectedCount > 0}
        <button type="button" class="action-link" onclick={clearAll}>
          {$t("Clear")}
        </button>
      {/if}
      {#if selectedCount < totalCount}
        <button type="button" class="action-link" onclick={selectAll}>
          {$t("Select all")}
        </button>
      {/if}
    </div>
  </div>

  {#if choices.length === 0}
    <NoOptionsAvailable />
  {:else}
    <div class="search-box">
      <svg
        class="search-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.7"
        stroke-linecap="round"
        stroke-linejoin="round"
        width="14"
        height="14"
        ><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg
      >
      <input
        type="text"
        bind:value={query}
        placeholder={$t("Search...")}
        class="search-input"
      />
      {#if query}
        <button
          type="button"
          class="search-clear"
          onclick={() => (query = "")}
          aria-label={$t("Clear search")}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
            width="11"
            height="11"><path d="M18 6 6 18M6 6l12 12" /></svg
          >
        </button>
      {/if}
    </div>

    {#if filteredOptions.length === 0}
      <div class="empty">
        {$t("No matches for")} <strong>"{query}"</strong>
      </div>
    {:else}
      <div class="groups">
        {#each groups as [letter, options]}
          <div class="group">
            <div class="letter">{letter}</div>
            <div class="options">
              {#each options as opt}
                <label class="option">
                  <input
                    type="checkbox"
                    value={opt.original}
                    checked={value.includes(opt.original)}
                    onchange={(e) =>
                      toggle(opt.original, e.currentTarget.checked)}
                  />
                  <span class="option-label">{opt.translated}</span>
                </label>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .grouped-array {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .title-row {
    display: flex;
    align-items: baseline;
    gap: 10px;
    min-width: 0;
  }

  .title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-1);
  }

  .count {
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-3);
  }

  .actions {
    display: flex;
    gap: 14px;
  }

  .action-link {
    background: transparent;
    border: 0;
    color: var(--accent);
    font-size: 12px;
    font-weight: 500;
    padding: 0;
    cursor: pointer;
  }

  .action-link:hover {
    text-decoration: underline;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    border-radius: 8px;
    background: var(--bg-2);
    border: 1px solid var(--line);
    transition: border-color var(--dur-1);
  }

  .search-box:focus-within {
    border-color: var(--accent);
  }

  .search-icon {
    color: var(--text-3);
    flex-shrink: 0;
  }

  .search-input {
    flex: 1;
    background: transparent;
    border: 0;
    outline: 0;
    color: var(--text-1);
    font-size: 13px;
    font-family: inherit;
    min-width: 0;
  }

  .search-clear {
    color: var(--text-3);
    background: transparent;
    border: 0;
    display: grid;
    place-items: center;
    border-radius: 4px;
    padding: 2px;
    cursor: pointer;
  }

  .search-clear:hover {
    color: var(--text-1);
  }

  .empty {
    padding: 24px;
    text-align: center;
    color: var(--text-3);
    font-size: 12.5px;
  }

  .empty strong {
    color: var(--text-2);
  }

  .groups {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .group {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .letter {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-4);
    padding: 4px 0 2px;
    border-bottom: 1px solid var(--line-soft);
  }

  .options {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 2px 8px;
  }

  .option {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 5px 6px;
    border-radius: 5px;
    cursor: pointer;
    transition: background var(--dur-1);
    min-width: 0;
  }

  .option:hover {
    background: var(--bg-hover);
  }

  .option input[type="checkbox"] {
    flex-shrink: 0;
    width: 14px;
    height: 14px;
    accent-color: var(--accent);
    cursor: pointer;
    margin: 0;
  }

  .option-label {
    font-size: 12.5px;
    color: var(--text-2);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .option:has(input:checked) .option-label {
    color: var(--text-1);
    font-weight: 500;
  }
</style>
