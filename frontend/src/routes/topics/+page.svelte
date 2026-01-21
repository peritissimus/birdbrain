<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchTopics, fetchTopicBookmarks, fetchTopicSummary, reclassifyAll, fetchStats } from '$lib/api';
	import type { Topic, Bookmark, Stats } from '$lib/types';

	interface TopicWithBookmarks extends Topic {
		bookmarks: Bookmark[];
		summary: string | null;
		summaryLoading: boolean;
		expanded: boolean;
	}

	let topics: TopicWithBookmarks[] = $state([]);
	let stats: Stats | null = $state(null);
	let loading = $state(true);
	let error: string | null = $state(null);
	let reclassifying = $state(false);
	let generatingSummaries = $state(false);
	let summaryProgress = $state({ current: 0, total: 0 });

	async function loadData() {
		loading = true;
		error = null;
		try {
			const [topicsRes, statsRes] = await Promise.all([fetchTopics(), fetchStats()]);
			stats = statsRes;

			// Load first 3 bookmarks for each topic
			const topicsWithBookmarks = await Promise.all(
				topicsRes.topics.slice(0, 20).map(async (topic) => {
					const res = await fetchTopicBookmarks(topic.name, 3);
					return {
						...topic,
						bookmarks: res.bookmarks,
						summary: null,
						summaryLoading: false,
						expanded: false
					};
				})
			);
			topics = topicsWithBookmarks;

			// Load summaries in background (3 at a time)
			loadSummariesInBatches();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	}

	async function loadSummariesInBatches() {
		const batchSize = 3;
		for (let i = 0; i < topics.length; i += batchSize) {
			const batch = topics.slice(i, i + batchSize);
			await Promise.all(
				batch.map(async (topic, idx) => {
					const actualIdx = i + idx;
					topics[actualIdx].summaryLoading = true;
					try {
						const res = await fetchTopicSummary(topic.name);
						topics[actualIdx].summary = res.summary;
					} catch {
						// Ignore errors for individual summaries
					} finally {
						topics[actualIdx].summaryLoading = false;
					}
				})
			);
		}
	}

	async function handleGenerateAllSummaries() {
		generatingSummaries = true;
		summaryProgress = { current: 0, total: topics.length };

		try {
			for (let i = 0; i < topics.length; i++) {
				topics[i].summaryLoading = true;
				summaryProgress.current = i + 1;

				try {
					const res = await fetchTopicSummary(topics[i].name);
					topics[i].summary = res.summary;
				} catch {
					// Continue on error
				} finally {
					topics[i].summaryLoading = false;
				}
			}
		} finally {
			generatingSummaries = false;
		}
	}

	async function handleReclassifyAll() {
		if (!confirm('This will reclassify all bookmarks. Continue?')) return;
		reclassifying = true;
		try {
			await reclassifyAll();
			setTimeout(loadData, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to reclassify';
		} finally {
			reclassifying = false;
		}
	}

	async function handleReclassifyFailed() {
		reclassifying = true;
		try {
			await reclassifyAll('failed');
			setTimeout(loadData, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to reclassify';
		} finally {
			reclassifying = false;
		}
	}

	function getTweetUrl(bookmark: Bookmark): string {
		return `https://x.com/${bookmark.author_handle}/status/${bookmark.rest_id}`;
	}

	onMount(loadData);
</script>

<svelte:head>
	<title>Topics - Birdbrain</title>
</svelte:head>

<div class="page">
	<header class="page-header">
		<div class="header-content">
			<a href="/" class="back-link" aria-label="Back to bookmarks">
				<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
					<path d="M7.414 13l5.043 5.04-1.414 1.42L3.586 12l7.457-7.46 1.414 1.42L7.414 11H21v2H7.414z" />
				</svg>
			</a>
			<h1>Topics Overview</h1>
		</div>
		<div class="header-actions">
			{#if stats && stats.failed > 0}
				<button class="btn btn-secondary" onclick={handleReclassifyFailed} disabled={reclassifying}>
					Retry {stats.failed} failed
				</button>
			{/if}
			<button class="btn btn-secondary" onclick={handleGenerateAllSummaries} disabled={generatingSummaries || loading}>
				{#if generatingSummaries}
					Generating ({summaryProgress.current}/{summaryProgress.total})
				{:else}
					Generate All Summaries
				{/if}
			</button>
			<button class="btn btn-primary" onclick={handleReclassifyAll} disabled={reclassifying}>
				{#if reclassifying}
					Reclassifying...
				{:else}
					Reclassify All
				{/if}
			</button>
		</div>
	</header>

	{#if stats}
		<div class="stats-summary">
			<div class="stat-card">
				<span class="stat-number">{stats.total}</span>
				<span class="stat-label">Total</span>
			</div>
			<div class="stat-card">
				<span class="stat-number success">{stats.completed}</span>
				<span class="stat-label">Classified</span>
			</div>
			<div class="stat-card">
				<span class="stat-number warning">{stats.pending}</span>
				<span class="stat-label">Pending</span>
			</div>
			<div class="stat-card">
				<span class="stat-number error">{stats.failed}</span>
				<span class="stat-label">Failed</span>
			</div>
			<div class="stat-card">
				<span class="stat-number">{topics.length}</span>
				<span class="stat-label">Topics</span>
			</div>
		</div>
	{/if}

	{#if error}
		<div class="error-banner">
			<span>{error}</span>
			<button onclick={loadData}>Retry</button>
		</div>
	{/if}

	<main class="topics-grid">
		{#if loading}
			<div class="loading">
				<div class="spinner"></div>
				<span>Loading topics...</span>
			</div>
		{:else if topics.length === 0}
			<div class="empty">
				<h3>No topics yet</h3>
				<p>Classify some bookmarks to see topics here</p>
			</div>
		{:else}
			{#each topics as topic}
				<section class="topic-card">
					<header class="topic-header">
						<a href="/?topic={encodeURIComponent(topic.name)}" class="topic-title">
							#{topic.name}
						</a>
						<span class="topic-count">{topic.count} bookmarks</span>
					</header>

					<div class="topic-summary">
						{#if topic.summaryLoading}
							<div class="summary-loading">
								<span class="mini-spinner"></span>
								Generating summary...
							</div>
						{:else if topic.summary}
							<p>{topic.summary}</p>
						{/if}
					</div>

					<div class="topic-bookmarks">
						{#each topic.bookmarks as bookmark}
							<a href={getTweetUrl(bookmark)} target="_blank" class="bookmark-preview">
								<div class="bookmark-meta">
									<span class="author">@{bookmark.author_handle}</span>
								</div>
								<p class="bookmark-text">{bookmark.text.slice(0, 120)}{bookmark.text.length > 120 ? '...' : ''}</p>
								{#if bookmark.summary}
									<p class="bookmark-summary">{bookmark.summary}</p>
								{/if}
							</a>
						{/each}
					</div>

					{#if topic.count > 3}
						<a href="/?topic={encodeURIComponent(topic.name)}" class="view-all">
							View all {topic.count} bookmarks
						</a>
					{/if}
				</section>
			{/each}
		{/if}
	</main>
</div>

<style>
	.page {
		max-width: 900px;
		margin: 0 auto;
		padding: 20px;
		min-height: 100vh;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 24px;
		padding-bottom: 16px;
		border-bottom: 1px solid var(--color-border);
	}

	.header-content {
		display: flex;
		align-items: center;
		gap: 16px;
	}

	.back-link {
		color: var(--color-text);
		padding: 8px;
		border-radius: 50%;
		transition: background 0.2s;
	}

	.back-link:hover {
		background: var(--color-surface);
		text-decoration: none;
	}

	.page-header h1 {
		margin: 0;
		font-size: 24px;
		font-weight: 800;
	}

	.header-actions {
		display: flex;
		gap: 12px;
	}

	.btn {
		padding: 10px 20px;
		border: none;
		border-radius: 9999px;
		font-weight: 700;
		font-size: 14px;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-primary {
		background: var(--color-primary);
		color: white;
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-hover);
	}

	.btn-secondary {
		background: var(--color-surface);
		color: var(--color-text);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-surface-hover);
	}

	.stats-summary {
		display: flex;
		gap: 16px;
		margin-bottom: 24px;
		flex-wrap: wrap;
	}

	.stat-card {
		background: var(--color-surface);
		border-radius: 12px;
		padding: 16px 24px;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.stat-number {
		font-size: 24px;
		font-weight: 800;
		color: var(--color-text);
	}

	.stat-number.success {
		color: var(--color-success);
	}

	.stat-number.warning {
		color: var(--color-warning);
	}

	.stat-number.error {
		color: var(--color-error);
	}

	.stat-label {
		font-size: 13px;
		color: var(--color-muted);
	}

	.error-banner {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px;
		background: rgba(244, 33, 46, 0.1);
		border-radius: 12px;
		margin-bottom: 24px;
		color: var(--color-error);
	}

	.error-banner button {
		background: var(--color-error);
		color: white;
		border: none;
		padding: 8px 16px;
		border-radius: 9999px;
		font-weight: 700;
		cursor: pointer;
	}

	.topics-grid {
		display: grid;
		gap: 20px;
	}

	.loading,
	.empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 60px 20px;
		text-align: center;
		color: var(--color-muted);
	}

	.spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--color-border);
		border-top-color: var(--color-primary);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
		margin-bottom: 16px;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.empty h3 {
		margin: 0 0 8px;
		color: var(--color-text);
	}

	.topic-card {
		background: var(--color-surface);
		border-radius: 16px;
		padding: 20px;
	}

	.topic-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: 16px;
	}

	.topic-title {
		font-size: 20px;
		font-weight: 800;
		color: var(--color-primary);
	}

	.topic-title:hover {
		text-decoration: underline;
	}

	.topic-count {
		font-size: 14px;
		color: var(--color-muted);
	}

	.topic-summary {
		margin-bottom: 16px;
		min-height: 24px;
	}

	.topic-summary p {
		margin: 0;
		font-size: 15px;
		color: var(--color-text-secondary);
		line-height: 1.5;
	}

	.summary-loading {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 13px;
		color: var(--color-muted);
	}

	.mini-spinner {
		width: 14px;
		height: 14px;
		border: 2px solid var(--color-border);
		border-top-color: var(--color-primary);
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	.topic-bookmarks {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.bookmark-preview {
		background: var(--color-bg);
		border-radius: 12px;
		padding: 12px 16px;
		text-decoration: none;
		transition: background 0.2s;
	}

	.bookmark-preview:hover {
		background: var(--color-surface-hover);
	}

	.bookmark-meta {
		margin-bottom: 6px;
	}

	.author {
		font-size: 14px;
		color: var(--color-muted);
	}

	.bookmark-text {
		margin: 0;
		font-size: 14px;
		color: var(--color-text);
		line-height: 1.4;
	}

	.bookmark-summary {
		margin: 8px 0 0;
		font-size: 13px;
		color: var(--color-text-secondary);
		font-style: italic;
	}

	.view-all {
		display: block;
		text-align: center;
		margin-top: 16px;
		padding: 12px;
		color: var(--color-primary);
		font-size: 14px;
		font-weight: 500;
		border-radius: 8px;
		transition: background 0.2s;
	}

	.view-all:hover {
		background: var(--color-primary-light);
		text-decoration: none;
	}
</style>
