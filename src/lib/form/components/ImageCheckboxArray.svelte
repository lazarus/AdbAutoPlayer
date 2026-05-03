<script lang="ts">
  import { t } from "$lib/i18n/i18n";
  import { updateCheckboxArray } from "$lib/form/checkboxHelper";
  import NoOptionsAvailable from "$lib/components/generic/NoOptionsAvailable.svelte";
  import type { ImageCheckboxArrayProps } from "$lib/form/types";

  let {
    choices,
    assetPath,
    value = $bindable(),
  }: ImageCheckboxArrayProps = $props();

  let query = $state("");

  const translatedChoices = $derived(
    (choices || []).map((c) => ({ original: c, translated: $t(c) })),
  );

  const filteredChoices = $derived(
    query.trim()
      ? translatedChoices.filter((c) =>
          c.translated.toLowerCase().includes(query.trim().toLowerCase()),
        )
      : translatedChoices,
  );

  function toggle(choice: string, checked: boolean) {
    value = updateCheckboxArray(value, choice, checked);
  }

  function clearAll() {
    value = [];
  }

  function selectAll() {
    value = (choices || []).slice();
  }

  const total = $derived(translatedChoices.length);
  const selected = $derived(Array.isArray(value) ? value.length : 0);
  const showSearch = $derived(total >= 10);
  const showActions = $derived(total > 1);
</script>

<div class="image-checkbox-array">
  {#if choices.length === 0}
    <NoOptionsAvailable />
  {:else}
    {#if showActions || showSearch}
      <div class="header">
        {#if showActions}
          <span class="count">{selected} / {total}</span>
          <div class="actions">
            {#if selected > 0}
              <button type="button" class="action-link" onclick={clearAll}>
                {$t("Clear")}
              </button>
            {/if}
            {#if selected < total}
              <button type="button" class="action-link" onclick={selectAll}>
                {$t("Select all")}
              </button>
            {/if}
          </div>
        {/if}
      </div>
    {/if}

    {#if showSearch}
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
    {/if}

    {#if filteredChoices.length === 0 && query}
      <div class="empty">
        {$t("No matches for")} <strong>"{query}"</strong>
      </div>
    {:else}
      <div class="cards">
        {#each filteredChoices as opt}
          {@const isChecked = Array.isArray(value)
            ? value.includes(opt.original)
            : false}
          <label class="card" class:checked={isChecked}>
            <input
              class="card-checkbox"
              type="checkbox"
              value={opt.original}
              checked={isChecked}
              onchange={(e) => toggle(opt.original, e.currentTarget.checked)}
            />
            <img
              src={`${assetPath}/${opt.original}.png`}
              alt={opt.translated}
              class="card-img"
              draggable="false"
            />
            <span class="card-label">{opt.translated}</span>
          </label>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .image-checkbox-array {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    min-height: 18px;
  }

  .count {
    font-family: var(--font-mono);
    font-size: 11.5px;
    color: var(--text-3);
  }

  .actions {
    display: flex;
    gap: 14px;
    margin-left: auto;
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
    padding: 20px;
    text-align: center;
    color: var(--text-3);
    font-size: 12.5px;
  }

  .empty strong {
    color: var(--text-2);
  }

  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
    gap: 8px;
  }

  .card {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px 6px 8px;
    border-radius: 8px;
    background: var(--bg-2);
    border: 1px solid var(--line);
    cursor: pointer;
    transition:
      background var(--dur-1),
      border-color var(--dur-1);
    min-width: 0;
  }

  .card:hover:not(.checked) {
    background: var(--bg-hover);
    border-color: color-mix(in oklab, var(--accent) 25%, var(--line));
  }

  .card.checked {
    background: color-mix(in oklab, var(--accent) 10%, var(--bg-1));
    border-color: color-mix(in oklab, var(--accent) 45%, transparent);
  }

  .card-checkbox {
    flex-shrink: 0;
    width: 14px;
    height: 14px;
    accent-color: var(--accent);
    cursor: pointer;
    margin: 0;
  }

  .card-img {
    width: 22px;
    height: 22px;
    object-fit: cover;
    border-radius: 4px;
    flex-shrink: 0;
  }

  .card-label {
    font-size: 12.5px;
    color: var(--text-2);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }

  .card.checked .card-label {
    color: var(--text-1);
    font-weight: 500;
  }
</style>
