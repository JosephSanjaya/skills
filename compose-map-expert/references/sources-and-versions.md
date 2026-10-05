# Sources, versions, docs

## Artifacts

```kotlin
implementation("com.google.maps.android:maps-compose:<v>")          // GoogleMap, Marker, MarkerComposable, MapEffect
implementation("com.google.maps.android:maps-compose-utils:<v>")    // Clustering, Street View metadata
implementation("com.google.maps.android:maps-compose-widgets:<v>")  // ScaleBar, DisappearingScaleBar
```

- Pulls matching `play-services-maps` + `android-maps-utils`; don't pin those separately unless required.
- Verified: maps-compose/-utils **8.6.0**, android-maps-utils **5.2.0**, play-services-maps **20.0.0**. README
  listed **9.0.0** latest (Oct 2026). Re-check `clustering.md` behaviour claims (`clearItems/addItems` loop,
  `onClusterManager` in `SideEffect`) on major bumps.

## Docs

- Context7: maps-compose **not** indexed. Useful IDs (`npx ctx7@latest docs <id> "<question>"`):
  - `/googlemaps/android-maps-utils`: ClusterManager, algorithms, renderer fields
  - `/googlemaps-samples/android-samples`: Compose snippets
  - `/websites/developer_android_develop_ui_compose_performance`: Compose phases, stability
- README: https://github.com/googlemaps/android-maps-compose (sample `MarkerClusteringActivity`)
- API ref: https://googlemaps.github.io/android-maps-compose

## Real sources (most reliable)

Render/cluster behaviour lives in sources, not docs. Unzip from the Gradle cache:

```bash
find ~/.gradle/caches/modules-2 \( -name "maps-compose-*-sources.jar" -o -name "maps-compose-utils-*-sources.jar" \
  -o -name "android-maps-utils-*-sources.jar" \) | grep <version>
mkdir -p /tmp/mc && cd /tmp/mc && unzip -oq <jar>
```

Read:
- `compose/clustering/Clustering.kt`: items loop, `onClusterManager`, renderer setup
- `compose/clustering/ClusterRenderer.kt`: `ComposeUiClusterRenderer`, `collectInvalidationsAndRerender`
- `compose/RememberComposeBitmapDescriptor.kt`: `MarkerComposable` render-once-by-keys
- `clustering/ClusterManager.kt`: `setAlgorithm`, `onCameraIdle`, `cluster()`
- `clustering/algo/NonHierarchicalViewBasedAlgorithm.kt`, `clustering/view/DefaultClusterRenderer.kt`

No sources jar → let the IDE download, or temporarily `idea { module { isDownloadSources = true } }`.
