<script lang="ts">
	import type { Topic } from '$lib/types';

	let {
		topics,
		selectedTopic,
		onSelect
	}: {
		topics: Topic[];
		selectedTopic: string | null;
		onSelect: (topic: string | null) => void;
	} = $props();
</script>

<div class="topic-filter">
	<h3>Topics</h3>
	<div class="topic-list">
		<button class="topic-btn" class:active={!selectedTopic} onclick={() => onSelect(null)}>
			<span class="topic-name">All bookmarks</span>
		</button>
		{#each topics.slice(0, 15) as topic}
			<button
				class="topic-btn"
				class:active={selectedTopic === topic.name}
				onclick={() => onSelect(topic.name)}
			>
				<span class="topic-name">#{topic.name}</span>
				<span class="topic-count">{topic.count}</span>
			</button>
		{/each}
	</div>
</div>

<style>
	.topic-filter {
		padding: 16px 0;
	}

	h3 {
		margin: 0 0 12px 16px;
		font-size: 20px;
		font-weight: 800;
		color: var(--color-text);
	}

	.topic-list {
		display: flex;
		flex-direction: column;
	}

	.topic-btn {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: 12px 16px;
		background: transparent;
		border: none;
		text-align: left;
		cursor: pointer;
		transition: background 0.2s;
	}

	.topic-btn:hover {
		background: var(--color-surface);
	}

	.topic-btn.active {
		background: var(--color-primary-light);
	}

	.topic-btn.active .topic-name {
		color: var(--color-primary);
		font-weight: 700;
	}

	.topic-name {
		font-size: 15px;
		color: var(--color-text);
	}

	.topic-count {
		font-size: 13px;
		color: var(--color-muted);
		background: var(--color-surface);
		padding: 2px 8px;
		border-radius: 9999px;
	}

	.topic-btn.active .topic-count {
		background: var(--color-primary);
		color: white;
	}
</style>
