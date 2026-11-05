# faq

**is shadlet production ready?**  provides a Python runtime and React
renderer, but session state is process-local and authentication is application
owned. Review [limitations](limitations.md) and verify that those boundaries
fit your deployment and persistence needs.

**does it require a registry?** no, built-in components ship with the package.
