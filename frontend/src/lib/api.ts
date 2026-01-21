import type { BookmarksResponse, TopicsResponse, Stats } from './types';

const API_BASE = 'http://localhost:8787';

export async function fetchBookmarks(
	limit = 50,
	offset = 0,
	topic?: string,
	query?: string
): Promise<BookmarksResponse> {
	const params = new URLSearchParams({
		limit: limit.toString(),
		offset: offset.toString()
	});
	if (topic) params.set('topic', topic);
	if (query) params.set('q', query);

	const res = await fetch(`${API_BASE}/api/bookmarks?${params}`);
	if (!res.ok) throw new Error('Failed to fetch bookmarks');
	return res.json();
}

export async function fetchTopics(): Promise<TopicsResponse> {
	const res = await fetch(`${API_BASE}/api/topics`);
	if (!res.ok) throw new Error('Failed to fetch topics');
	return res.json();
}

export async function fetchStats(): Promise<Stats> {
	const res = await fetch(`${API_BASE}/api/stats`);
	if (!res.ok) throw new Error('Failed to fetch stats');
	return res.json();
}

export async function triggerClassification(): Promise<{ status: string; task_id?: string }> {
	const res = await fetch(`${API_BASE}/api/tweets/classify`, { method: 'POST' });
	return res.json();
}

export async function reclassifyBookmark(restId: string): Promise<{ status: string }> {
	const res = await fetch(`${API_BASE}/api/bookmarks/${restId}/reclassify`, { method: 'POST' });
	return res.json();
}

export async function reclassifyAll(status?: string): Promise<{ status: string; count: number }> {
	const params = status ? `?status=${status}` : '';
	const res = await fetch(`${API_BASE}/api/bookmarks/reclassify-all${params}`, { method: 'POST' });
	return res.json();
}

export async function deleteBookmark(restId: string): Promise<{ status: string }> {
	const res = await fetch(`${API_BASE}/api/bookmarks/${restId}`, { method: 'DELETE' });
	return res.json();
}

export async function fetchTopicBookmarks(
	topicName: string,
	limit = 5
): Promise<{ topic: string; bookmarks: import('./types').Bookmark[]; total: number }> {
	const params = new URLSearchParams({ limit: limit.toString() });
	const res = await fetch(`${API_BASE}/api/topics/${encodeURIComponent(topicName)}/bookmarks?${params}`);
	if (!res.ok) throw new Error('Failed to fetch topic bookmarks');
	return res.json();
}

export async function fetchTopicSummary(
	topicName: string
): Promise<{ topic: string; summary: string | null }> {
	const res = await fetch(`${API_BASE}/api/topics/${encodeURIComponent(topicName)}/summary`);
	if (!res.ok) throw new Error('Failed to fetch topic summary');
	return res.json();
}
