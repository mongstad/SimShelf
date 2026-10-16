# Third-party notices

SimShelf is distributed under the [MIT license](LICENSE).

The packaged browser bundle contains React, React DOM, and Scheduler, distributed
under their respective MIT licenses by Meta Platforms, Inc. and affiliates.
Their complete copyright and license texts, with installed package versions, are
included in [THIRD_PARTY_LICENSES.txt](src/simshelf/static/assets/THIRD_PARTY_LICENSES.txt).
The bundle's extracted license comments remain in
[app.js.LEGAL.txt](src/simshelf/static/assets/app.js.LEGAL.txt).
Both files ship alongside the browser assets in the Python distribution.

Run `pnpm install --frozen-lockfile` followed by `pnpm run build` to regenerate
the browser assets and full notices from the locked packages. The build fails if
a required package license cannot be read. Review notices when updating bundled
dependencies. Python and frontend development dependencies retain their own
licenses in their installed distributions; they are not vendored into this tree.
