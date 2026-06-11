# Fix Company Context Injection Logic

## Todo
- [x] Analyze the problem: template uses hardcoded `[TO BE CONFIRMED]`, context mapping is incomplete, [TBC:key] markers don't exist in template
- [ ] Phase 1: Fix context_data mapping in reports.py - add all missing fields, fix incorrect key names
- [ ] Phase 2: Enhance `_validate_placeholder_value()` in template_engine.py with stricter validation
  - Add country-name rejection for non-country string fields
  - Add cross-field section awareness check
  - Add employee/common value pattern detection for wrong fields
- [ ] Phase 3: Replace `[TO BE CONFIRMED]` with `[TBC:key]` markers in template HTML
  - Map each `[TO BE CONFIRMED]` to the correct FIELD_REGISTRY key
  - Leave unmappable ones as `[TO BE CONFIRMED]`
- [ ] Phase 4: Fix template direct attribute usage (template.employee_count, template.company_sector) to use context data
- [ ] Phase 5: Add comprehensive tests for validation, injection, and cross-field rejection
- [ ] Phase 6: Run existing tests to ensure nothing breaks
