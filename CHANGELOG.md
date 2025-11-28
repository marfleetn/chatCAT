# Changelog

All notable changes to chatCAT will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2025-01-28

### Added
- **Grok support** (grok.com) - Full conversation capture
- **DeepSeek support** (chat.deepseek.com) - Full conversation capture
- Position-based message sorting for accurate conversation order

### Changed
- Updated ChatLLM URL pattern from `chatllm.abacus.ai` to `apps.abacus.ai`
- Improved Poe capture function with better role detection
- Enhanced message deduplication across all platforms

### Fixed
- Poe: Fixed crash caused by SVG elements with non-string className
- ChatLLM: Updated selectors for new UI structure
- Gemini: Fixed Trusted Types violation blocking indicator creation

## [2.3.3] - 2025-01-27

### Fixed
- **Trusted Types compatibility** for Gemini - Replaced innerHTML with DOM methods
- Indicator now appears correctly on Gemini
- All platforms now use CSP-compliant element creation

## [2.3.2] - 2025-01-27

### Fixed
- Claude: Removed user avatar/initial from captured messages
- Added regex cleanup to remove stray single letters at message start

## [2.3.1] - 2025-01-27

### Added
- Multiple DOM append targets for better indicator visibility
- Retry mechanism for indicator creation (up to 10 attempts)
- Enhanced CSS specificity with !important flags
- MutationObserver for SPA navigation detection

### Fixed
- Indicator visibility on Claude, Gemini, and ChatLLM
- FTS (Full-Text Search) trigger errors causing notes save to fail
- Tags not displaying after creation

## [2.3.0] - 2025-01-26

### Added
- Tag management system with colour-coded tags
- Notes feature for adding personal annotations to conversations
- Full-text search with relevance ranking
- Search term highlighting in results

### Changed
- Dashboard redesigned with MS-DOS aesthetic
- Improved search performance with SQLite FTS5

## [2.2.0] - 2025-01-25

### Added
- Draggable indicator with position memory
- Click indicator to open dashboard
- MS-DOS theme styling

### Fixed
- Drag vs click detection improved
- Position saving to localStorage

## [2.1.0] - 2025-01-24

### Added
- Perplexity support
- Poe support
- Manus support
- ChatLLM support

### Changed
- Refactored platform detection
- Improved message role detection

## [2.0.0] - 2025-01-23

### Added
- Web dashboard for searching conversations
- SQLite database storage
- Platform filtering
- Date range filtering
- Export to CSV

### Changed
- Complete rewrite of capture system
- New API endpoint structure

## [1.0.0] - 2025-01-20

### Added
- Initial release
- Claude support
- ChatGPT support
- Gemini support
- Basic conversation capture
- Floating indicator

---

## Version History Summary

| Version | Date | Highlights |
|---------|------|------------|
| 2.4.0 | 2025-01-28 | Grok & DeepSeek support, ChatLLM/Poe fixes |
| 2.3.3 | 2025-01-27 | Trusted Types fix for Gemini |
| 2.3.2 | 2025-01-27 | Avatar removal from Claude messages |
| 2.3.1 | 2025-01-27 | Indicator visibility & FTS fixes |
| 2.3.0 | 2025-01-26 | Tags, notes, FTS search |
| 2.2.0 | 2025-01-25 | Draggable indicator, MS-DOS theme |
| 2.1.0 | 2025-01-24 | Perplexity, Poe, Manus, ChatLLM |
| 2.0.0 | 2025-01-23 | Web dashboard, SQLite storage |
| 1.0.0 | 2025-01-20 | Initial release |
