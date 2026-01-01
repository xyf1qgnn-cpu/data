# Expert Detail Questions

**Phase**: Detail Requirements
**Date**: 2026-01-01 15:28
**Total Questions**: 5

## Q1: Should the GUI preserve the existing directory structure (files/, NotInput/, Excluded/) or allow custom output locations?
**Default if unknown:** Preserve existing structure with optional customization
**Reasoning:** The existing workflow expects specific directories. We should maintain backward compatibility while allowing users to choose custom locations via GUI if desired. This balances stability with flexibility.

## Q2: Should the progress bar show overall progress (files processed/total) or detailed per-file progress with time estimates?
**Default if unknown:** Both - overall progress bar with detailed per-file status in log area
**Reasoning:** Users need to see both high-level progress and detailed file-by-file status. The progress bar can show overall completion while the log area shows current file being processed, extraction status, and any issues.

## Q3: Should the application include a "dry run" or preview mode that extracts data without calling the API?
**Default if unknown:** No - focus on core functionality first
**Reasoning:** While preview mode could be useful for testing, it adds complexity. The initial version should focus on reliable batch processing with API calls. Preview mode could be added in a future update if needed.

## Q4: Should error handling include automatic retry for failed API calls with configurable retry limits?
**Default if unknown:** Yes - implement basic retry logic (3 attempts with exponential backoff)
**Reasoning:** Network issues and API rate limits are common. Basic retry logic improves reliability without significant complexity. Users should see retry attempts in the log area.

## Q5: Should the application include export options beyond Excel (CSV, JSON) in the initial version?
**Default if unknown:** No - maintain existing Excel export only
**Reasoning:** The existing workflow produces styled Excel files with validation highlighting. Adding additional formats increases complexity and testing requirements. Excel export meets the core need for data review and manual checking.