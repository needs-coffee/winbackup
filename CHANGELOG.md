# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## 0.2.0-beta - 25-06-2022
### Added 
- Autoconfirm CLI flag (-y/--autoconfirm)
- Add option for all targets at cli (-a/--all)
- detect if platform is not windows and quit. Only functions on windows. 
- option to Tar before 7z for all targets
- Warning added for short password length with interactive config
- Keys missing in config file are filled with default values
### Changed
- upgrade 7z from version 19 to version 22 (~20% speed increase)
- Plex dedicated functions removed, backed up as a standard folder
- check plex database size correctly and decide on splitting - don't always force splitting.
- Refactoring of backup functions.
- Removed split-force config option
### Fixed
- Fix performance bug if compression level = 0 (store) (remove md + m0 cli flags)


## 0.1.7-beta
### Fixed 
- Fix for virtualbox config
### Added
- GH CI/CD


## 0.1.0-beta - 03-05-2022
### Added
- Initial Release
