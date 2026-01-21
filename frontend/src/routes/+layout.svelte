<script lang="ts">
	let { children } = $props();
</script>

{@render children()}

<style>
	:global(:root) {
		/* Twitter Dark Theme */
		--color-bg: #000000;
		--color-surface: #16181c;
		--color-surface-hover: #1d1f23;
		--color-border: #2f3336;
		--color-text: #e7e9ea;
		--color-text-secondary: #71767b;
		--color-muted: #71767b;
		--color-primary: #1d9bf0;
		--color-primary-hover: #1a8cd8;
		--color-primary-light: rgba(29, 155, 240, 0.1);
		--color-success: #00ba7c;
		--color-warning: #ffad1f;
		--color-error: #f4212e;
		--color-link: #1d9bf0;
	}

	:global(*) {
		box-sizing: border-box;
	}

	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial,
			sans-serif;
		background: var(--color-bg);
		color: var(--color-text);
		line-height: 1.5;
		-webkit-font-smoothing: antialiased;
	}

	:global(button) {
		font-family: inherit;
	}

	:global(a) {
		color: var(--color-link);
		text-decoration: none;
	}

	:global(a:hover) {
		text-decoration: underline;
	}

	:global(::selection) {
		background: var(--color-primary);
		color: white;
	}
</style>
