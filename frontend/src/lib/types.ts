export interface Bookmark {
	id: number;
	rest_id: string;
	text: string;
	author_handle: string;
	author_name: string;
	created_at: string | null;
	topics: string[];
	summary: string | null;
	classification_status: 'pending' | 'completed' | 'failed';
	media_urls: string | null;
	quoted_status_id: string | null;
}

export interface BookmarksResponse {
	bookmarks: Bookmark[];
	total: number;
	limit: number;
	offset: number;
}

export interface Topic {
	name: string;
	count: number;
}

export interface TopicsResponse {
	topics: Topic[];
}

export interface Stats {
	total: number;
	pending: number;
	completed: number;
	failed: number;
}
