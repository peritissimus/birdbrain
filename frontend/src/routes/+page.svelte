<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchBookmarks, fetchTopics, fetchStats, triggerClassification } from '$lib/api';
	import type { Bookmark, Topic, Stats } from '$lib/types';
	import BookmarkCard from '$lib/components/BookmarkCard.svelte';
	import StatsBar from '$lib/components/StatsBar.svelte';
	import TopicFilter from '$lib/components/TopicFilter.svelte';

	let bookmarks: Bookmark[] = $state([]);
	let topics: Topic[] = $state([]);
	let stats: Stats | null = $state(null);
	let selectedTopic: string | null = $state(null);
	let searchQuery = $state('');
	let loading = $state(true);
	let classifying = $state(false);
	let error: string | null = $state(null);
	let total = $state(0);
	let offset = $state(0);
	const limit = 50;
	let searchTimeout: ReturnType<typeof setTimeout> | null = null;

	async function loadData() {
		loading = true;
		error = null;
		try {
			const [bookmarksRes, topicsRes, statsRes] = await Promise.all([
				fetchBookmarks(limit, offset, selectedTopic || undefined, searchQuery || undefined),
				fetchTopics(),
				fetchStats()
			]);
			bookmarks = bookmarksRes.bookmarks;
			total = bookmarksRes.total;
			topics = topicsRes.topics;
			stats = statsRes;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		} finally {
			loading = false;
		}
	}

	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		searchQuery = target.value;
		offset = 0;

		if (searchTimeout) clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			loadData();
		}, 300);
	}

	function clearSearch() {
		searchQuery = '';
		offset = 0;
		loadData();
	}

	async function handleClassify() {
		classifying = true;
		try {
			await triggerClassification();
			setTimeout(loadData, 2000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Classification failed';
		} finally {
			classifying = false;
		}
	}

	function handleTopicSelect(topic: string | null) {
		selectedTopic = topic;
		offset = 0;
		loadData();
	}

	function loadMore() {
		offset += limit;
		loadData();
	}

	onMount(loadData);
</script>

<svelte:head>
	<title>Birdbrain</title>
</svelte:head>

<div class="app">
	<aside class="sidebar">
		<div class="logo">
			<svg viewBox="0 0 24 24" width="32" height="32" fill="var(--color-primary)">
				<path
					d="M23.643 4.937c-.835.37-1.732.62-2.675.733.962-.576 1.7-1.49 2.048-2.578-.9.534-1.897.922-2.958 1.13-.85-.904-2.06-1.47-3.4-1.47-2.572 0-4.658 2.086-4.658 4.66 0 .364.042.718.12 1.06-3.873-.195-7.304-2.05-9.602-4.868-.4.69-.63 1.49-.63 2.342 0 1.616.823 3.043 2.072 3.878-.764-.025-1.482-.234-2.11-.583v.06c0 2.257 1.605 4.14 3.737 4.568-.392.106-.803.162-1.227.162-.3 0-.593-.028-.877-.082.593 1.85 2.313 3.198 4.352 3.234-1.595 1.25-3.604 1.995-5.786 1.995-.376 0-.747-.022-1.112-.065 2.062 1.323 4.51 2.093 7.14 2.093 8.57 0 13.255-7.098 13.255-13.254 0-.2-.005-.402-.014-.602.91-.658 1.7-1.477 2.323-2.41z"
				/>
			</svg>
			<span>Birdbrain</span>
		</div>

		<nav class="nav">
			<a href="/" class="nav-item active">
				<svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
					<path
						d="M12 3.53l9.472 9.644a.75.75 0 0 1-1.069 1.052l-1.153-1.174v7.698a.75.75 0 0 1-.75.75H14a.75.75 0 0 1-.75-.75v-5.5h-2.5v5.5a.75.75 0 0 1-.75.75H5.5a.75.75 0 0 1-.75-.75v-7.698l-1.153 1.174a.75.75 0 1 1-1.069-1.052L12 3.53z"
					/>
				</svg>
				<span>Bookmarks</span>
			</a>
			<a href="/topics" class="nav-item">
				<svg viewBox="0 0 24 24" width="26" height="26" fill="currentColor">
					<path
						d="M12.003 21.234l-.292-.248c-3.473-2.953-5.683-5.196-6.694-6.728C4.006 12.727 3.5 11.307 3.5 9.86c0-2.758 2.168-4.86 5.007-4.86 1.775 0 3.218.865 4.176 2.044.393-.483.87-.905 1.41-1.25a5.328 5.328 0 012.407-.794c2.839 0 5.007 2.102 5.007 4.86 0 1.447-.506 2.867-1.517 4.398-1.011 1.532-3.221 3.775-6.694 6.728l-.293.248zM4 10a1 1 0 100-2 1 1 0 000 2zm2-5a1 1 0 100-2 1 1 0 000 2zm4-2a1 1 0 100-2 1 1 0 000 2z"
					/>
				</svg>
				<span>Topics</span>
			</a>
		</nav>

		<div class="sidebar-topics">
			<TopicFilter {topics} {selectedTopic} onSelect={handleTopicSelect} />
		</div>
	</aside>

	<main class="main">
		<header class="header">
			<h1>
				{#if searchQuery}
					Search: "{searchQuery}"
				{:else if selectedTopic}
					#{selectedTopic}
				{:else}
					Bookmarks
				{/if}
			</h1>
			{#if searchQuery || selectedTopic}
				<span class="result-count">{total} results</span>
			{/if}
		</header>

		<StatsBar {stats} onClassify={handleClassify} {classifying} />

		{#if error}
			<div class="error">
				<span>{error}</span>
				<button onclick={loadData}>Retry</button>
			</div>
		{/if}

		<section class="feed">
			{#if loading}
				<div class="loading">
					<div class="spinner"></div>
					<span>Loading bookmarks...</span>
				</div>
			{:else if bookmarks.length === 0}
				<div class="empty">
					<svg viewBox="0 0 24 24" width="48" height="48" fill="var(--color-muted)">
						<path
							d="M19.9 23.5H4.1c-.6 0-1.1-.5-1.1-1.1V1.6c0-.6.5-1.1 1.1-1.1h15.8c.6 0 1.1.5 1.1 1.1v20.8c0 .6-.5 1.1-1.1 1.1zM17.5 3H6.5v18h11V3z"
						/>
					</svg>
					<h3>No bookmarks yet</h3>
					<p>Use the browser extension to sync your Twitter bookmarks</p>
				</div>
			{:else}
				{#each bookmarks as bookmark (bookmark.id)}
					<BookmarkCard {bookmark} onUpdate={loadData} />
				{/each}

				{#if bookmarks.length < total}
					<button class="load-more" onclick={loadMore}>
						Show more
					</button>
				{/if}
			{/if}
		</section>
	</main>

	<aside class="right-sidebar">
		<div class="search-box">
			<svg viewBox="0 0 24 24" width="18" height="18" fill="var(--color-muted)">
				<path
					d="M10.25 3.75c-3.59 0-6.5 2.91-6.5 6.5s2.91 6.5 6.5 6.5c1.795 0 3.419-.726 4.596-1.904 1.178-1.177 1.904-2.801 1.904-4.596 0-3.59-2.91-6.5-6.5-6.5zm-8.5 6.5c0-4.694 3.806-8.5 8.5-8.5s8.5 3.806 8.5 8.5c0 1.986-.682 3.815-1.824 5.262l4.781 4.781-1.414 1.414-4.781-4.781c-1.447 1.142-3.276 1.824-5.262 1.824-4.694 0-8.5-3.806-8.5-8.5z"
				/>
			</svg>
			<input
				type="text"
				placeholder="Search bookmarks"
				value={searchQuery}
				oninput={handleSearch}
			/>
			{#if searchQuery}
				<button class="clear-search" onclick={clearSearch} aria-label="Clear search">
					<svg viewBox="0 0 24 24" width="16" height="16" fill="currentColor">
						<path
							d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"
						/>
					</svg>
				</button>
			{/if}
		</div>

		<div class="info-box">
			<h3>About Birdbrain</h3>
			<p>
				Your Twitter bookmarks, automatically organized with AI-generated topics and summaries.
			</p>
			<div class="info-links">
				<a href="https://github.com" target="_blank">GitHub</a>
				<span>·</span>
				<a href="https://x.com" target="_blank">Twitter</a>
			</div>
		</div>
	</aside>
</div>

<style>
	.app {
		display: grid;
		grid-template-columns: 275px 600px 350px;
		max-width: 1265px;
		margin: 0 auto;
		min-height: 100vh;
	}

	/* Sidebar */
	.sidebar {
		position: sticky;
		top: 0;
		height: 100vh;
		padding: 12px;
		border-right: 1px solid var(--color-border);
		display: flex;
		flex-direction: column;
	}

	.logo {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 12px;
		font-size: 20px;
		font-weight: 800;
		color: var(--color-text);
	}

	.nav {
		margin-top: 8px;
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 20px;
		padding: 12px;
		border-radius: 9999px;
		font-size: 20px;
		color: var(--color-text);
		text-decoration: none;
		transition: background 0.2s;
	}

	.nav-item:hover {
		background: var(--color-surface);
	}

	.nav-item.active {
		font-weight: 700;
	}

	.sidebar-topics {
		flex: 1;
		overflow-y: auto;
		margin-top: 16px;
	}

	/* Main */
	.main {
		border-right: 1px solid var(--color-border);
		min-height: 100vh;
	}

	.header {
		padding: 16px 20px;
		position: sticky;
		top: 0;
		background: rgba(0, 0, 0, 0.65);
		backdrop-filter: blur(12px);
		z-index: 20;
		border-bottom: 1px solid var(--color-border);
	}

	.header h1 {
		margin: 0;
		font-size: 20px;
		font-weight: 800;
	}

	.result-count {
		font-size: 13px;
		color: var(--color-muted);
		font-weight: 400;
	}

	.error {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 16px 20px;
		background: rgba(244, 33, 46, 0.1);
		border-bottom: 1px solid var(--color-border);
		color: var(--color-error);
	}

	.error button {
		background: var(--color-error);
		color: white;
		border: none;
		padding: 8px 16px;
		border-radius: 9999px;
		font-weight: 700;
		cursor: pointer;
	}

	.feed {
		min-height: 50vh;
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

	.loading .spinner {
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
		margin: 16px 0 8px;
		font-size: 18px;
		color: var(--color-text);
	}

	.empty p {
		margin: 0;
		font-size: 15px;
	}

	.load-more {
		width: 100%;
		padding: 16px;
		background: transparent;
		border: none;
		border-bottom: 1px solid var(--color-border);
		color: var(--color-primary);
		font-size: 15px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.2s;
	}

	.load-more:hover {
		background: var(--color-primary-light);
	}

	/* Right Sidebar */
	.right-sidebar {
		padding: 12px 20px;
		position: sticky;
		top: 0;
		height: 100vh;
	}

	.search-box {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 12px 16px;
		background: var(--color-surface);
		border-radius: 9999px;
		margin-bottom: 16px;
	}

	.search-box input {
		flex: 1;
		background: transparent;
		border: none;
		outline: none;
		color: var(--color-text);
		font-size: 15px;
	}

	.search-box input::placeholder {
		color: var(--color-muted);
	}

	.clear-search {
		background: none;
		border: none;
		padding: 4px;
		cursor: pointer;
		color: var(--color-muted);
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		transition: background 0.2s, color 0.2s;
	}

	.clear-search:hover {
		background: var(--color-surface-hover);
		color: var(--color-text);
	}

	.info-box {
		background: var(--color-surface);
		border-radius: 16px;
		padding: 16px;
	}

	.info-box h3 {
		margin: 0 0 8px;
		font-size: 20px;
		font-weight: 800;
	}

	.info-box p {
		margin: 0 0 12px;
		color: var(--color-text-secondary);
		font-size: 15px;
		line-height: 1.4;
	}

	.info-links {
		display: flex;
		gap: 8px;
		font-size: 14px;
	}

	.info-links a {
		color: var(--color-primary);
	}

	.info-links span {
		color: var(--color-muted);
	}

	/* Responsive */
	@media (max-width: 1280px) {
		.app {
			grid-template-columns: 88px 1fr;
		}

		.logo span,
		.nav-item span,
		.sidebar-topics {
			display: none;
		}

		.logo {
			justify-content: center;
		}

		.nav-item {
			justify-content: center;
			padding: 12px;
		}

		.right-sidebar {
			display: none;
		}
	}

	@media (max-width: 700px) {
		.app {
			grid-template-columns: 1fr;
		}

		.sidebar {
			display: none;
		}
	}
</style>
