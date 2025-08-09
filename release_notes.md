## Cross-Platform Support Release

### New Features
- Full Cross-Platform Compatibility: Now supports Unix/Linux, macOS, and Windows
- Platform Abstraction Layer: Clean architecture with proper class separation and specialization
- Windows Experimental Support: Basic Windows compatibility with appropriate warnings
- Platform-Aware Directory Handling:
  - Linux/macOS: ~/.local/share/dosctl/
  - Windows: %LOCALAPPDATA%/dosctl/

### Technical Improvements
- Implemented abstract base classes for platform abstraction
- Added Factory pattern for automatic platform detection
- Created DOSBox launcher abstraction layer
- Windows subprocess optimizations (console window suppression)
- Maintained full backward compatibility

### Windows Support Notice
Windows support is experimental and has not been extensively tested. Linux and macOS remain the primary supported platforms.

### Architecture Changes
- New src/dosctl/lib/platform/ module with platform-specific implementations
- New src/dosctl/lib/dosbox/ module for DOSBox launcher abstraction
- Updated existing modules to use platform abstraction while preserving existing APIs

### Compatibility
- All existing functionality preserved
- No breaking changes to existing commands or configuration
- Backward compatible directory access functions maintained

This release represents a significant architectural improvement while maintaining complete compatibility with existing installations.
