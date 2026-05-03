<script lang="ts">
  import IconX from "$lib/components/icons/feather/IconX.svelte";
  import { t } from "$lib/i18n/i18n";
  import SettingsSectionHeader from "./SettingsSectionHeader.svelte";
  import NoOptionsAvailable from "$lib/components/generic/NoOptionsAvailable.svelte";
  import type { TaskListProps } from "$lib/form/types";

  let { choices, value = $bindable() }: TaskListProps = $props();

  let draggedItem = $state<string | null>(null);
  let draggedFromSelected = $state(false);
  let draggedIndex = $state(-1);
  let currentDragPosition = $state<
    "above-first" | "between" | "below-last" | null
  >(null);
  let isOverContainer = $state(false);

  function handleDragStart(
    e: DragEvent,
    task: string,
    fromSelected: boolean,
    index: number = -1,
  ) {
    draggedItem = task;
    draggedFromSelected = fromSelected;
    draggedIndex = index;
    if (e.dataTransfer) {
      e.dataTransfer.effectAllowed = fromSelected ? "move" : "copy";
      e.dataTransfer.setData("text/plain", task);
    }
    currentDragPosition = null;
    isOverContainer = false;
  }

  let dropIndicatorPos = $state<{
    index: number;
    position: "before" | "after";
  } | null>(null);

  function handleDragOver(e: DragEvent) {
    e.preventDefault();
    if (!draggedItem) return;

    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = draggedFromSelected ? "move" : "copy";
    }

    const container = e.currentTarget as HTMLElement;
    const items = container.querySelectorAll('[draggable="true"]');

    if (items.length === 0) {
      dropIndicatorPos = null;
      currentDragPosition = null;
      isOverContainer = true;
      return;
    }

    const firstItemRect = items[0].getBoundingClientRect();
    if (e.clientY < firstItemRect.top + firstItemRect.height * 0.25) {
      dropIndicatorPos = { index: 0, position: "before" };
      currentDragPosition = "above-first";
      isOverContainer = true;
      return;
    }

    const lastItemRect = items[items.length - 1].getBoundingClientRect();
    if (e.clientY > lastItemRect.bottom - lastItemRect.height * 0.25) {
      dropIndicatorPos = { index: items.length - 1, position: "after" };
      currentDragPosition = "below-last";
      isOverContainer = true;
      return;
    }

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      const rect = item.getBoundingClientRect();
      const middleY = rect.top + rect.height / 2;

      if (e.clientY < middleY) {
        dropIndicatorPos = { index: i, position: "before" };
        currentDragPosition = "between";
        isOverContainer = true;
        return;
      } else if (e.clientY < rect.bottom) {
        dropIndicatorPos = { index: i, position: "after" };
        currentDragPosition = "between";
        isOverContainer = true;
        return;
      }
    }

    dropIndicatorPos = null;
    currentDragPosition = null;
    isOverContainer = true;
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    if (!draggedItem) return;

    if (!isOverContainer) {
      resetDragState();
      return;
    }

    if (value.length === 0) {
      if (!draggedFromSelected || !value.includes(draggedItem)) {
        value = [...value, draggedItem];
      }
      resetDragState();
      return;
    }

    let insertIndex = value.length;

    if (dropIndicatorPos) {
      const { index, position } = dropIndicatorPos;
      insertIndex = position === "before" ? index : index + 1;
    } else if (currentDragPosition === "above-first") {
      insertIndex = 0;
    } else if (currentDragPosition === "below-last") {
      insertIndex = value.length;
    }

    insertIndex = Math.max(0, Math.min(insertIndex, value.length));

    if (draggedFromSelected) {
      if (
        draggedIndex === insertIndex ||
        (draggedIndex + 1 === insertIndex && insertIndex < value.length)
      ) {
        resetDragState();
        return;
      }

      const newValue = [...value];
      const [movedItem] = newValue.splice(draggedIndex, 1);
      const adjustedIndex =
        draggedIndex < insertIndex ? insertIndex - 1 : insertIndex;
      newValue.splice(adjustedIndex, 0, movedItem);
      value = newValue;
    } else {
      const newValue = [...value];
      newValue.splice(insertIndex, 0, draggedItem);
      value = newValue;
    }

    resetDragState();
  }

  function resetDragState() {
    dropIndicatorPos = null;
    draggedItem = null;
    draggedFromSelected = false;
    draggedIndex = -1;
    currentDragPosition = null;
    isOverContainer = false;
  }

  function handleDragLeave(e: DragEvent) {
    const container = e.currentTarget as HTMLElement;
    const relatedTarget = e.relatedTarget as HTMLElement | null;

    if (!relatedTarget || !container.contains(relatedTarget)) {
      isOverContainer = false;
      dropIndicatorPos = null;
      currentDragPosition = null;
    }
  }

  function handleContainerDragOver(e: DragEvent, index: number) {
    e.preventDefault();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = draggedFromSelected ? "move" : "copy";
    }

    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
    const middleY = rect.top + rect.height / 2;
    dropIndicatorPos = {
      index,
      position: e.clientY < middleY ? "before" : "after",
    };
    currentDragPosition = "between";
    isOverContainer = true;
  }

  function removeTask(index: number) {
    value = value.filter((_, i) => i !== index);
  }

  function clearList() {
    if (confirm($t("Are you sure you want to clear all tasks?"))) {
      value = [];
    }
  }

  function addTask(task: string) {
    value = [...value, task];
  }
</script>

<div class="task-list-root">
  <div class="task-list-inner">
    <div class="tasks-header">
      <SettingsSectionHeader text={$t("Tasks")} />
      {#if choices.length > 0}
        <button class="btn-danger" type="button" onclick={clearList}>
          {$t("Clear Tasks")}
        </button>
      {/if}
    </div>

    {#if choices.length === 0}
      <NoOptionsAvailable />
    {:else}
      <div class="columns-grid">
        <!-- Column headers -->
        <div class="col-header">
          <div class="col-bar col-bar-available"></div>
          <h3 class="col-title">{$t("Available Tasks")}</h3>
        </div>
        <div class="col-header">
          <div class="col-bar col-bar-selected"></div>
          <h3 class="col-title">{$t("Selected Tasks")}</h3>
        </div>

        <!-- Available tasks panel -->
        <div class="task-panel">
          {#if choices.length === 0}
            <div class="empty-center">
              <p class="muted-text">{$t("No tasks available")}</p>
            </div>
          {:else}
            {#each choices as task}
              <div
                class="task-card task-card-available"
                draggable="true"
                ondragstart={(e) => handleDragStart(e, task, false)}
                ondblclick={() => addTask(task)}
                role="button"
                tabindex="0"
                title="Double-click to add, or drag to position"
              >
                <div class="task-card-inner">
                  <div class="task-dot task-dot-available"></div>
                  <p class="task-label">{$t(task)}</p>
                </div>
              </div>
            {/each}
          {/if}
        </div>

        <!-- Selected tasks panel -->
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
          class="task-panel task-panel-selected"
          ondragover={handleDragOver}
          ondrop={(e) => handleDrop(e)}
          ondragleave={handleDragLeave}
          ondragenter={() => (isOverContainer = true)}
        >
          {#if value.length === 0}
            <div class="empty-center">
              <div class="empty-icon">
                <div class="empty-ring"></div>
              </div>
              <p class="muted-text">{$t("Drag tasks here to add them")}</p>
            </div>
          {:else}
            {#if currentDragPosition === "above-first"}
              <div class="drop-indicator"></div>
            {/if}

            {#each value as task, index}
              {#if dropIndicatorPos?.index === index && dropIndicatorPos?.position === "before" && currentDragPosition === "between"}
                <div class="drop-indicator"></div>
              {/if}

              <div
                class="task-card task-card-selected"
                draggable="true"
                ondragstart={(e) => handleDragStart(e, task, true, index)}
                ondragover={(e) => handleContainerDragOver(e, index)}
                role="button"
                tabindex="0"
              >
                <div class="task-card-inner">
                  <div class="task-badge">{index + 1}</div>
                  <p class="task-label">{$t(task)}</p>
                </div>
                <button
                  class="remove-btn"
                  type="button"
                  onclick={() => removeTask(index)}
                  title="Remove task"
                >
                  <IconX size={16} />
                </button>
              </div>

              {#if dropIndicatorPos?.index === index && dropIndicatorPos?.position === "after" && currentDragPosition === "between"}
                <div class="drop-indicator"></div>
              {/if}
            {/each}

            {#if currentDragPosition === "below-last"}
              <div class="drop-indicator"></div>
            {/if}
          {/if}
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .task-list-root {
    padding: 24px;
  }

  .task-list-inner {
    max-width: 72rem;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .tasks-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px;
    border-radius: var(--radius-lg);
    background: var(--bg-2);
    border: 1px solid var(--line-soft);
  }

  .btn-danger {
    padding: 8px 16px;
    border-radius: var(--radius);
    font-size: 13px;
    font-weight: 600;
    background: color-mix(in oklab, var(--err) 85%, var(--bg-2));
    color: var(--text-1);
    border: 1px solid color-mix(in oklab, var(--err) 60%, transparent);
    transition:
      background var(--dur-1),
      filter var(--dur-1);
  }

  .btn-danger:hover {
    filter: brightness(1.15);
  }

  .columns-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px 32px;
  }

  @media (max-width: 768px) {
    .columns-grid {
      grid-template-columns: 1fr;
    }
  }

  .col-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 4px;
  }

  .col-bar {
    height: 4px;
    width: 32px;
    border-radius: 999px;
    flex-shrink: 0;
  }

  .col-bar-available {
    background: var(--text-3);
  }

  .col-bar-selected {
    background: var(--accent);
  }

  .col-title {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    color: var(--text-1);
  }

  .task-panel {
    min-height: 300px;
    border-radius: var(--radius);
    border: 1px solid var(--line);
    background: var(--bg-1);
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    transition: border-color var(--dur-1);
  }

  .task-panel-selected {
    border-color: color-mix(in oklab, var(--accent) 40%, var(--line));
    background: color-mix(in oklab, var(--accent) 5%, var(--bg-1));
  }

  .empty-center {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: var(--accent-ghost);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .empty-ring {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    border: 2px solid var(--accent);
    opacity: 0.6;
  }

  .muted-text {
    font-size: 12px;
    color: var(--text-4);
    text-align: center;
    margin: 0;
  }

  .task-card {
    border-radius: var(--radius-sm);
    padding: 8px;
    cursor: grab;
    transition:
      background var(--dur-1),
      transform var(--dur-1),
      box-shadow var(--dur-1);
    position: relative;
  }

  .task-card:hover {
    transform: scale(1.02);
    box-shadow: 0 2px 8px oklch(0 0 0 / 0.2);
  }

  .task-card:active {
    transform: scale(0.97);
    cursor: grabbing;
  }

  .task-card-available {
    background: var(--bg-2);
  }

  .task-card-available:hover {
    background: var(--bg-hover);
  }

  .task-card-selected {
    background: color-mix(in oklab, var(--accent) 12%, var(--bg-1));
  }

  .task-card-selected:hover {
    background: color-mix(in oklab, var(--accent) 18%, var(--bg-1));
  }

  .task-card-inner {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .task-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-left: 12px;
  }

  .task-dot-available {
    background: var(--text-3);
  }

  .task-badge {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: var(--accent);
    color: var(--text-1);
    font-family: var(--font-mono);
    font-size: 11px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    margin-left: 12px;
  }

  .task-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-1);
    margin: 0;
    flex: 1;
  }

  .remove-btn {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 24px;
    height: 24px;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-3);
    background: transparent;
    opacity: 0;
    transition:
      opacity var(--dur-1),
      background var(--dur-1),
      color var(--dur-1),
      transform var(--dur-1);
  }

  .task-card:hover .remove-btn {
    opacity: 1;
  }

  .remove-btn:hover {
    background: var(--err);
    color: var(--text-1);
    transform: translateY(-50%) scale(1.1);
  }

  .remove-btn:active {
    transform: translateY(-50%) scale(0.95);
  }

  .drop-indicator {
    height: 2px;
    border-radius: 999px;
    background: var(--accent);
    margin: 2px 0;
  }
</style>
