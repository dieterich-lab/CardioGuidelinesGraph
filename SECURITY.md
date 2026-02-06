# Security Policy

## Automated Security Updates

This repository uses [Dependabot](https://docs.github.com/en/code-security/dependabot) to automatically monitor and update dependencies for security vulnerabilities.

### How it works:
1. **Weekly scans**: Dependabot checks for vulnerable dependencies every week
2. **Automated PRs**: When vulnerabilities are found, Dependabot creates pull requests with fixes
3. **Review process**: PRs are assigned to the `dieterich-lab` team for review
4. **Safe updates**: Only patch and minor version updates are applied automatically

### What to expect:
- **Security alerts**: GitHub will notify maintainers of critical vulnerabilities
- **Dependabot PRs**: Automated pull requests will appear for dependency updates
- **Review required**: All security updates should be reviewed before merging

### Manual security checks:
- Visit the [Security tab](https://github.com/dieterich-lab/CardioGuidelinesGraph/security) on GitHub
- Check Dependabot alerts and security advisories
- Review and merge Dependabot pull requests promptly

### Configuration:
- Dependabot is configured in `.github/dependabot.yml`
- Updates Python dependencies and GitHub Actions weekly
- Limited to 10 open PRs for Python dependencies, 5 for GitHub Actions

## Reporting Security Issues

If you discover a security vulnerability, please report it by:
1. Creating an issue in this repository
2. Emailing the maintainers directly
3. Using GitHub's security advisory feature

## Current Status

GitHub's automated security scan currently reports 43 vulnerabilities across the dependency tree. These will be addressed through the automated Dependabot process.