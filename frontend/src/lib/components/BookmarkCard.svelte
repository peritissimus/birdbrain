<script lang="ts">
	import type { Bookmark } from '$lib/types';
	import { reclassifyBookmark, deleteBookmark } from '$lib/api';

	let { bookmark, onUpdate }: { bookmark: Bookmark; onUpdate?: () => void } = $props();

	let actionLoading = $state(false);

	async function handleReclassify(e: Event) {
		e.stopPropagation();
		actionLoading = true;
		try {
			await reclassifyBookmark(bookmark.rest_id);
			if (onUpdate) onUpdate();
		} finally {
			actionLoading = false;
		}
	}

	async function handleDelete(e: Event) {
		e.stopPropagation();
		if (!confirm('Delete this bookmark?')) return;
		actionLoading = true;
		try {
			await deleteBookmark(bookmark.rest_id);
			if (onUpdate) onUpdate();
		} finally {
			actionLoading = false;
		}
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffHours = diffMs / (1000 * 60 * 60);
		const diffDays = diffMs / (1000 * 60 * 60 * 24);

		if (diffHours < 24) {
			return `${Math.floor(diffHours)}h`;
		} else if (diffDays < 7) {
			return `${Math.floor(diffDays)}d`;
		} else {
			return date.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric'
			});
		}
	}

	function getStatusIcon(status: string): string {
		switch (status) {
			case 'completed':
				return '✓';
			case 'pending':
				return '○';
			case 'failed':
				return '!';
			default:
				return '';
		}
	}

	function getTweetUrl(): string {
		return `https://x.com/${bookmark.author_handle}/status/${bookmark.rest_id}`;
	}

	function getQuotedTweetUrl(): string | null {
		if (!bookmark.quoted_status_id) return null;
		// Use /i/status/ format which redirects to the correct user
		return `https://x.com/i/status/${bookmark.quoted_status_id}`;
	}
</script>

<article class="tweet">
	<div class="tweet-content">
		<header class="tweet-header">
			<a href="https://x.com/{bookmark.author_handle}" target="_blank" class="author-info">
				<span class="author-name">{bookmark.author_name}</span>
				<span class="author-handle">@{bookmark.author_handle}</span>
			</a>
			<span class="separator">·</span>
			<a href={getTweetUrl()} target="_blank" class="tweet-time">
				{formatDate(bookmark.created_at)}
			</a>
		</header>

		<div class="tweet-text">{bookmark.text}</div>

		{#if bookmark.quoted_status_id}
			<a href={getQuotedTweetUrl()} target="_blank" class="quoted-tweet-link" onclick={(e) => e.stopPropagation()}>
				<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
					<path d="M14.23 2.854c.98-.977 2.56-.977 3.54 0l3.38 3.378c.97.977.97 2.559 0 3.536L9.91 21H3v-6.91L14.23 2.854zm2.12 1.414c-.19-.195-.51-.195-.7 0L5 14.914V19h4.09L19.73 8.354c.2-.196.2-.512 0-.708l-3.38-3.378zM14.75 19l-2 2H21v-2h-6.25z" />
				</svg>
				<span>View quoted tweet</span>
			</a>
		{/if}

		{#if bookmark.summary}
			<div class="ai-summary">
				<div class="ai-badge">
					<svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor">
						<path
							d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"
						/>
					</svg>
					<span>AI Summary</span>
				</div>
				<p>{bookmark.summary}</p>
			</div>
		{/if}

		<footer class="tweet-footer">
			{#if bookmark.topics.length > 0}
				<div class="topics">
					{#each bookmark.topics as topic}
						<span class="topic">#{topic}</span>
					{/each}
				</div>
			{/if}
			<div class="actions">
				<button
					class="action-btn"
					onclick={handleReclassify}
					disabled={actionLoading}
					title="Reclassify"
				>
					<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
						<path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46C19.54 15.03 20 13.57 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74C4.46 8.97 4 10.43 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z" />
					</svg>
				</button>
				<button
					class="action-btn action-delete"
					onclick={handleDelete}
					disabled={actionLoading}
					title="Delete"
				>
					<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
						<path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z" />
					</svg>
				</button>
				<span class="status status-{bookmark.classification_status}">
					{getStatusIcon(bookmark.classification_status)}
				</span>
			</div>
		</footer>
	</div>
</article>

<style>
	.tweet {
		padding: 16px;
		border-bottom: 1px solid var(--color-border);
		transition: background 0.2s;
		cursor: pointer;
	}

	.tweet:hover {
		background: var(--color-surface);
	}

	.tweet-content {
		min-width: 0;
	}

	.tweet-header {
		display: flex;
		align-items: center;
		gap: 4px;
		margin-bottom: 4px;
	}

	.author-info {
		display: flex;
		align-items: center;
		gap: 4px;
		text-decoration: none;
	}

	.author-info:hover .author-name {
		text-decoration: underline;
	}

	.author-name {
		font-weight: 700;
		color: var(--color-text);
	}

	.author-handle {
		color: var(--color-muted);
	}

	.separator {
		color: var(--color-muted);
	}

	.tweet-time {
		color: var(--color-muted);
		text-decoration: none;
	}

	.tweet-time:hover {
		text-decoration: underline;
	}

	.tweet-text {
		color: var(--color-text);
		font-size: 15px;
		line-height: 1.5;
		white-space: pre-wrap;
		word-break: break-word;
		margin-bottom: 12px;
	}

	.quoted-tweet-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 8px 12px;
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		color: var(--color-primary);
		font-size: 13px;
		font-weight: 500;
		margin-bottom: 12px;
		transition: background 0.2s;
	}

	.quoted-tweet-link:hover {
		background: var(--color-primary-light);
		text-decoration: none;
	}

	.ai-summary {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		border-radius: 16px;
		padding: 12px 16px;
		margin-bottom: 12px;
	}

	.ai-badge {
		display: flex;
		align-items: center;
		gap: 6px;
		color: var(--color-primary);
		font-size: 13px;
		font-weight: 600;
		margin-bottom: 6px;
	}

	.ai-summary p {
		margin: 0;
		color: var(--color-text-secondary);
		font-size: 14px;
		line-height: 1.4;
	}

	.tweet-footer {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.action-btn {
		background: none;
		border: none;
		padding: 6px;
		border-radius: 50%;
		cursor: pointer;
		color: var(--color-muted);
		transition: background 0.2s, color 0.2s;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.action-btn:hover:not(:disabled) {
		background: var(--color-primary-light);
		color: var(--color-primary);
	}

	.action-btn:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.action-delete:hover:not(:disabled) {
		background: rgba(244, 33, 46, 0.1);
		color: var(--color-error);
	}

	.topics {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
	}

	.topic {
		color: var(--color-primary);
		font-size: 14px;
		font-weight: 400;
	}

	.topic:hover {
		text-decoration: underline;
		cursor: pointer;
	}

	.status {
		font-size: 12px;
		font-weight: 600;
		width: 20px;
		height: 20px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.status-completed {
		color: var(--color-success);
		background: rgba(0, 186, 124, 0.1);
	}

	.status-pending {
		color: var(--color-warning);
		background: rgba(255, 173, 31, 0.1);
	}

	.status-failed {
		color: var(--color-error);
		background: rgba(244, 33, 46, 0.1);
	}
</style>
