# migration guide: 0.6.x to 0.7.0

## overview

shadlet 0.7.0 is a focused performance and verification release. It preserves protocol version 2 and maintains source compatibility with 0.6.x applications. The primary changes are lazy renderer adapters, predictable chunk names, a generated component compatibility matrix, and automated quality gates.

## breaking changes

**none**. shadlet 0.7.0 maintains full backward compatibility with 0.6.x applications.

## performance improvements

### renderer bundle optimization

the renderer's JavaScript bundle has been optimized through code-splitting:

- **main entry chunk**: 1,590.49kB to 1,060.3kB minified; 483.47kB to 327.9kB gzip
- **total renderer JavaScript**: 2,036.4kB minified; 573.0kB gzip across all chunks
- **lazy-loaded chunks**: chart ~429kB / 125kB gzip, calendar ~75kB / 23kB gzip, carousel ~23kB / 9kB gzip
- **mechanism**: chart, calendar/date picker, and carousel adapters use `React.lazy` behind a suspense boundary; Vite `manualChunks` gives the emitted chunks predictable names

**impact**: initial application load time is significantly faster. applications that don't use charts, calendars, or carousels benefit immediately without code changes.

### what you need to do

**nothing**. the browser automatically loads the required chunks when your application uses these components. existing applications will see faster initial load times after upgrading to 0.7.0.

## build and CI improvements

### automated bundle budget checks

the CI pipeline now enforces bundle size budgets:

- entry chunk: 1,100kB minified / 345kB gzip
- total JavaScript: 2,150kB minified / 610kB gzip
- required lazy chunks: chart, calendar, carousel, icon-data

**for maintainers**: `npm run check:bundle` now runs in CI and will fail the build if budgets are exceeded. this prevents unintentional bundle regressions.

**for application developers**: no action required. these checks run during shadlet development and release, not when you build your applications.

### protocol fixtures

the shared protocol test fixtures now use version 0.7.0 for consistency. pydantic and zod continue to validate the same protocol v2 contracts.

**what you need to do**: nothing. protocol version 2 is unchanged, and both 0.6.x and 0.7.0 clients and servers are compatible.

## upgrade path

### step 1: upgrade the package

```bash
pip install --upgrade shadlet
```

or with uv:

```bash
uv pip install --upgrade shadlet
```

### step 2: verify your application

start your application and verify that it loads correctly:

```bash
python main.py
```

open your application in a browser and interact with your components. charts, calendars, and carousels will now load their JavaScript on demand, but behavior remains identical.

### step 3: check network activity (optional)

open your browser's developer tools network tab and observe the chunk loading:

- the initial page load should be noticeably faster
- when you first interact with a Chart, the `chart-*.js` chunk will load
- when you first interact with a Calendar or DatePicker, the `calendar-*.js` chunk will load
- when you first interact with a Carousel, the `carousel-*.js` chunk will load

## component compatibility

0.7.0 keeps the 0.6.0 component APIs and adds the remaining upstream surfaces: `DirectionProvider` (serialized as `Direction`), declarative `Toast` through sonner, and `ScrollArea` coverage from `shadlet.layout`. all 56 pinned upstream components now have a Python type and renderer adapter. the generated [compatibility matrix](../components/compatibility-matrix.md) records exact runtime and verification support; entries remain `partial` where the vendored component exposes richer behavior than Shadlet maps. the [component catalogue](../components/catalogue.md) and [limitations](../limitations.md) documents remain accurate.

## known issues and limitations

no new limitations were introduced in 0.7.0. the [limitations](../limitations.md) document continues to describe the verified scope and boundaries.

## rollback

if you encounter any issues, you can roll back to 0.6.0:

```bash
pip install shadlet==0.6.0
```

please report any problems through [GitHub issues](https://github.com/programmersd21/shadlet/issues).

## future releases

shadlet 0.7.0 establishes the infrastructure for ongoing bundle optimization and quality enforcement. future releases will build on this foundation while maintaining protocol and API compatibility where possible.
