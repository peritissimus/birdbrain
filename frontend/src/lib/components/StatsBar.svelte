<script lang="ts">
	import type { Stats } from '$lib/types';

	let {
		stats,
		onClassify,
		classifying = false
	}: {
		stats: Stats | null;
		onClassify: () => void;
		classifying?: boolean;
	} = $props();
</script>

<div class="stats-bar">
	<div class="stats">
		{#if stats}
			<div class="stat">
				<span class="stat-value">{stats.total}</span>
				<span class="stat-label">Bookmarks</span>
			</div>
			<div class="stat">
				<span class="stat-value completed">{stats.completed}</span>
				<span class="stat-label">Classified</span>
			</div>
			{#if stats.pending > 0}
				<div class="stat">
					<span class="stat-value pending">{stats.pending}</span>
					<span class="stat-label">Pending</span>
				</div>
			{/if}
			{#if stats.failed > 0}
				<div class="stat">
					<span class="stat-value failed">{stats.failed}</span>
					<span class="stat-label">Failed</span>
				</div>
			{/if}
		{/if}
	</div>
	{#if stats && stats.pending > 0}
		<button class="classify-btn" onclick={onClassify} disabled={classifying}>
			{#if classifying}
				<span class="spinner"></span>
				Classifying...
			{:else}
				<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
					<path
						d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
					/>
				</svg>
				Classify {stats.pending} pending
			{/if}
		</button>
	{/if}
</div>

<style>
	.stats-bar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px 20px;
		border-bottom: 1px solid var(--color-border);
		background: var(--color-bg);
		position: sticky;
		top: 0;
		z-index: 10;
	}

	.stats {
		display: flex;
		gap: 24px;
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.stat-value {
		font-size: 18px;
		font-weight: 700;
		color: var(--color-text);
	}

	.stat-value.completed {
		color: var(--color-success);
	}

	.stat-value.pending {
		color: var(--color-warning);
	}

	.stat-value.failed {
		color: var(--color-error);
	}

	.stat-label {
		font-size: 13px;
		color: var(--color-muted);
	}

	.classify-btn {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 20px;
		background: var(--color-primary);
		color: white;
		border: none;
		border-radius: 9999px;
		font-weight: 700;
		font-size: 15px;
		cursor: pointer;
		transition: background 0.2s;
	}

	.classify-btn:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	.classify-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.spinner {
		width: 16px;
		height: 16px;
		border: 2px solid rgba(255, 255, 255, 0.3);
		border-top-color: white;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
</style>
