# Changelog

# [1.10.0](https://github.com/xesco/dosctl/compare/v1.9.4...v1.10.0) (2026-09-14)


### Features

* add LocalFileCollection that reads games from a local directory ([bf7a917](https://github.com/xesco/dosctl/commit/bf7a917236c061fe0ad05880b4169ae618a22542))

## [1.9.4](https://github.com/xesco/dosctl/compare/v1.9.3...v1.9.4) (2026-06-09)


### Bug Fixes

* register the version subcommand ([4bf0992](https://github.com/xesco/dosctl/commit/4bf09925740a920cb418026c3e53079d090cf29a))
* use typing.List for Python 3.8 compatibility ([a6bd898](https://github.com/xesco/dosctl/commit/a6bd898c6a06128e1d4ca8dc5ea185e98622279e))
* verify download size and index game lookups ([458e776](https://github.com/xesco/dosctl/commit/458e7765f3459b2f14632bb6a614d3eff43dd2f3))

## [1.9.3](https://github.com/xesco/dosctl/compare/v1.9.2...v1.9.3) (2026-03-24)


### Bug Fixes

* extract symlink-flagged ZIP entries as regular files ([d50ebc2](https://github.com/xesco/dosctl/commit/d50ebc2ca8795ec9614d49177f2e17bf5c7739ae))

## [1.9.2](https://github.com/xesco/dosctl/compare/v1.9.1...v1.9.2) (2026-03-22)


### Bug Fixes

* clean up aliases and saved commands on delete ([daf280e](https://github.com/xesco/dosctl/commit/daf280ee62341a9e0c0e90b9a8dc25603408e71e))

## [1.9.1](https://github.com/xesco/dosctl/compare/v1.9.0...v1.9.1) (2026-03-22)


### Bug Fixes

* prevent zip slip and symlink attacks during game extraction ([2a44b59](https://github.com/xesco/dosctl/commit/2a44b593dfe66aa07572784e78668ceed5728a06))

# [1.9.0](https://github.com/xesco/dosctl/compare/v1.8.0...v1.9.0) (2026-03-06)


### Features

* store game name in aliases.json for efficient alias list display ([bea1108](https://github.com/xesco/dosctl/commit/bea11086407ee189fac5a26daa525a5a2b828ffa))

# [1.8.0](https://github.com/xesco/dosctl/compare/v1.7.0...v1.8.0) (2026-03-01)


### Bug Fixes

* remove --download-only flag from play command ([0ffb30f](https://github.com/xesco/dosctl/commit/0ffb30f19f1fc2fcf0c3de568274ad55fb0f3a71))


### Features

* auto-detect per-game dosbox.conf in install directory ([e7e4f8e](https://github.com/xesco/dosctl/commit/e7e4f8e971cb63a82344d78e2e1b5c9e961ffce6))

# [1.7.0](https://github.com/xesco/dosctl/compare/v1.6.0...v1.7.0) (2026-03-01)


### Features

* add --download-only flag to play command ([9b748ac](https://github.com/xesco/dosctl/commit/9b748aca841b011140711d7bbd1c47004b315e63))
* add alias command for game IDs ([09f7ecf](https://github.com/xesco/dosctl/commit/09f7ecf37960e2f4a4c26306a1fd6bb14da8966c))
* add info command ([c66ab74](https://github.com/xesco/dosctl/commit/c66ab74f647c14e256eff670bdaae96aa4b6141c))

# [1.6.0](https://github.com/xesco/dosctl/compare/v1.5.0...v1.6.0) (2026-02-12)


### Features

* add --no-exec flag to net host command for debugging ([38c1360](https://github.com/xesco/dosctl/commit/38c13606b4839cb78f47ad8bbc219f49ea497813))

# [1.5.0](https://github.com/xesco/dosctl/compare/v1.4.0...v1.5.0) (2026-02-12)


### Features

* add --no-exec flag to play command for debugging ([e5012a8](https://github.com/xesco/dosctl/commit/e5012a87645230e30ac1139980af6c51a8d342e6))

# [1.4.0](https://github.com/xesco/dosctl/compare/v1.3.1...v1.4.0) (2026-02-11)


### Bug Fixes

* improve UPnP error messages to reassure users with manual port forwarding ([61e2415](https://github.com/xesco/dosctl/commit/61e241541cc2afddd55cc5d0f019e0d6e5fecbf4))
* improve UPnP error reporting and retry with lease_duration=0 ([8f102bb](https://github.com/xesco/dosctl/commit/8f102bbd93f2ee00d2dd635c359d1ef1417491d8))


### Features

* add 'dosctl net' command for IPX multiplayer over LAN ([f76ab30](https://github.com/xesco/dosctl/commit/f76ab301a30beb629e043c95e9796c539ee25eb7))
* add internet play with discovery codes, UPnP, and host options ([e3d2ae2](https://github.com/xesco/dosctl/commit/e3d2ae29387f5667643f5b55b5e7867bf3720af1))
* detect CGNAT and show actionable warning when UPnP fails ([c0c234b](https://github.com/xesco/dosctl/commit/c0c234b07cc53eb5506cddd93ee6dc9e13946f1f))
* verify UPnP port mapping with GetSpecificPortMappingEntry ([8901713](https://github.com/xesco/dosctl/commit/8901713be2deb9c99adbddf2aefd40ee4b13ec95))

## [1.3.1](https://github.com/xesco/dosctl/compare/v1.3.0...v1.3.1) (2026-02-11)


### Bug Fixes

* update play command help text from "Runs" to "Plays" ([7c2abf6](https://github.com/xesco/dosctl/commit/7c2abf6013eed2c92a04b56cc1bb37ab88fd77f3))

# [1.3.0](https://github.com/xesco/dosctl/compare/v1.2.1...v1.3.0) (2026-02-10)


### Features

* rename `run` subcommand to `play` ([6a8b442](https://github.com/xesco/dosctl/commit/6a8b442c454e1c67cc4b535cf96c7b3c0c7f35e1))

## [1.2.1](https://github.com/xesco/dosctl/compare/v1.2.0...v1.2.1) (2026-02-10)


### Bug Fixes

* cd into subdirectory before launching executables in DOSBox ([493f08e](https://github.com/xesco/dosctl/commit/493f08e4c6fbd98b463ab9c29a1c290beb8fedd1))
* return relative paths for executables in subdirectories ([72d0f15](https://github.com/xesco/dosctl/commit/72d0f156a3f0d093382bb57db4b0c6928c0d9131))

# [1.2.0](https://github.com/xesco/dosctl/compare/v1.1.5...v1.2.0) (2026-02-09)


### Features

* add -a/--floppy flag to mount game directory as A: drive ([1c98d0a](https://github.com/xesco/dosctl/commit/1c98d0a8196cb4d9c08b5be968564ac70679fe73))

## [1.1.5](https://github.com/xesco/dosctl/compare/v1.1.4...v1.1.5) (2026-02-09)


### Bug Fixes

* fix bugs, remove dead code, and improve code quality ([046b9bc](https://github.com/xesco/dosctl/commit/046b9bc9d813cc4f3f88e2a83768de95fa67e0fa))

## [1.1.4](https://github.com/xesco/dosctl/compare/v1.1.3...v1.1.4) (2025-08-09)


### Bug Fixes

* improve semantic-release deployment logic ([88085ec](https://github.com/xesco/dosctl/commit/88085ecd97fdc28f3380ae3e180a72e6040b9d85))

## [1.1.3](https://github.com/xesco/dosctl/compare/v1.1.2...v1.1.3) (2025-08-09)


### Bug Fixes

* improve release detection by comparing git SHA before/after semantic-release ([4d24bfc](https://github.com/xesco/dosctl/commit/4d24bfcc614d077fd3c6ccd2d68ca4b45c310881))

## [1.1.2](https://github.com/xesco/dosctl/compare/v1.1.1...v1.1.2) (2025-08-09)


### Bug Fixes

* only deploy to PyPI when semantic-release publishes a release ([ef1df52](https://github.com/xesco/dosctl/commit/ef1df52e9f23ed8f5e1b2b3f230de62c3fd1d8f9))

## [1.1.1](https://github.com/xesco/dosctl/compare/v1.1.0...v1.1.1) (2025-08-09)


### Bug Fixes

* add git plugin to semantic-release for version commits ([1bad443](https://github.com/xesco/dosctl/commit/1bad4434429c40373cc9b1fdef3828f1a4a27e44))
* configure semantic-release for proper version management ([a0b064a](https://github.com/xesco/dosctl/commit/a0b064a33557a6da935885c173be0034e5eba3d6))

# [1.1.0](https://github.com/xesco/dosctl/compare/v1.0.0...v1.1.0) (2025-08-09)


### Features

* complete semantic release automation setup ([25a89c1](https://github.com/xesco/dosctl/commit/25a89c1d0974b3bb5a7f78fb01ef20438d2a6968))

# [1.0.0](https://github.com/xesco/dosctl/compare/v0.2.1...v1.0.0) (2025-08-09)


### Bug Fixes

* resolve semantic-release permissions and trusted publisher setup ([ea43500](https://github.com/xesco/dosctl/commit/ea435006e7832b1fd0f260d7c6f5a51ef10a5121))
* simplify semantic-release configuration for reliability ([ee1dc9a](https://github.com/xesco/dosctl/commit/ee1dc9a7f12ec72ce98e7f32dfb6defc671da664))
* simplify semantic-release to basic working configuration ([bab5076](https://github.com/xesco/dosctl/commit/bab5076f8e99dc505870d459eded65ebc18e9347))


### Features

* add semantic release automation ([58fb68f](https://github.com/xesco/dosctl/commit/58fb68fd8d962e404284dfa719a2dc5e012e79e5))


### BREAKING CHANGES

* all future releases will use semantic versioning based on conventional commits

## [0.2.1] - 2025-08-09

### Features
- Add -v/--version flag to display version information

### Bug Fixes
- Fix integration tests by properly mocking path constants
- Improve test isolation with better mocking strategies

### Tests
- All 46 tests now pass successfully

## [0.2.0] - 2025-08-09

### Features
- Cross-platform support for Windows and Unix-like systems
- Proper directory paths for different operating systems
- Enhanced game installation and management

### Bug Fixes
- Fixed Windows path handling in configuration

## [0.1.0] - 2025-08-09

### Features
- Initial release of dosctl
- Command-line interface for managing DOS games
- Support for archive.org collections
- Game search, installation, and execution capabilities
- DOSBox integration
