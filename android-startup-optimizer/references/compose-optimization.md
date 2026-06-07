# Jetpack Compose Startup Optimization

Compose-specific patterns for minimizing initial composition and rendering time.

## Composition Phases

Compose has three phases:
1. **Composition** - Build UI tree, read state
2. **Layout** - Measure and position elements
3. **Drawing** - Render to canvas

**Goal:** Minimize work in Composition phase during startup.

## Defer Heavy Composition

### Lazy Composition

```kotlin
@Composable
fun MainScreen() {
    var showHeavyFeature by remember { mutableStateOf(false) }
    
    Column {
        // Always composed - lightweight
        TopBar()
        MainContent()
        
        // Only composed when needed
        if (showHeavyFeature) {
            HeavyFeatureScreen()
        }
        
        Button(onClick = { showHeavyFeature = true }) {
            Text("Load Feature")
        }
    }
}
```

### Delayed Composition

```kotlin
@Composable
fun HomeScreen() {
    var showBottomSheet by remember { mutableStateOf(false) }
    
    LaunchedEffect(Unit) {
        // Wait for main content to render
        delay(500)
        showBottomSheet = true
    }
    
    Scaffold(
        bottomBar = {
            if (showBottomSheet) {
                BottomNavigationBar()
            }
        }
    ) {
        MainContent()
    }
}
```

## State Management

### derivedStateOf for Expensive Calculations

```kotlin
@Composable
fun ScrollableList(items: List<Item>) {
    val listState = rememberLazyListState()
    
    // BAD: Recomposes on every scroll
    val isScrolled = listState.firstVisibleItemIndex > 0
    
    // GOOD: Only recomposes when result changes
    val isScrolled by remember {
        derivedStateOf {
            listState.firstVisibleItemIndex > 0
        }
    }
    
    LazyColumn(state = listState) {
        items(items) { item ->
            ItemRow(item, isScrolled)
        }
    }
}
```

### Stable Collections

```kotlin
// BAD: List causes recomposition on every change
@Composable
fun ItemList(items: List<Item>) {
    items.forEach { item ->
        ItemRow(item)
    }
}

// GOOD: ImmutableList prevents unnecessary recompositions
@Composable
fun ItemList(items: ImmutableList<Item>) {
    items.forEach { item ->
        ItemRow(item)
    }
}

// Usage
@HiltViewModel
class MainViewModel @Inject constructor() : ViewModel() {
    val items = MutableStateFlow(persistentListOf<Item>())
    
    fun addItem(item: Item) {
        items.value = items.value.add(item)
    }
}
```

## Modifier Optimization

### Lambda Modifiers for Phase Skipping

```kotlin
// BAD: Reads state in Composition phase
@Composable
fun AnimatedBox(offset: Int) {
    Box(
        modifier = Modifier.offset(x = offset.dp)
    )
}

// GOOD: Reads state in Layout phase
@Composable
fun AnimatedBox(offset: Int) {
    Box(
        modifier = Modifier.offset { IntOffset(offset, 0) }
    )
}
```

### Reuse Modifiers

```kotlin
// BAD: Creates new modifier on every recomposition
@Composable
fun ItemRow(item: Item) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp)
            .background(Color.White)
    ) {
        Text(item.title)
    }
}

// GOOD: Reuse modifier
private val itemModifier = Modifier
    .fillMaxWidth()
    .padding(16.dp)
    .background(Color.White)

@Composable
fun ItemRow(item: Item) {
    Row(modifier = itemModifier) {
        Text(item.title)
    }
}
```

## LazyColumn Optimization

### Key for Stable Items

```kotlin
@Composable
fun FeedScreen(items: List<Post>) {
    LazyColumn {
        items(
            items = items,
            key = { it.id } // Stable key prevents unnecessary recomposition
        ) { post ->
            PostCard(post)
        }
    }
}
```

### Content Type for Heterogeneous Lists

```kotlin
@Composable
fun MixedList(items: List<ListItem>) {
    LazyColumn {
        items(
            items = items,
            key = { it.id },
            contentType = { it.type } // Helps Compose reuse compositions
        ) { item ->
            when (item) {
                is TextItem -> TextCard(item)
                is ImageItem -> ImageCard(item)
                is VideoItem -> VideoCard(item)
            }
        }
    }
}
```

## Image Loading

### Async Image Loading with Coil

```kotlin
@Composable
fun ProfileImage(url: String) {
    AsyncImage(
        model = ImageRequest.Builder(LocalContext.current)
            .data(url)
            .crossfade(true)
            .size(200, 200) // Resize to display size
            .memoryCacheKey(url)
            .diskCacheKey(url)
            .build(),
        contentDescription = "Profile",
        modifier = Modifier.size(200.dp)
    )
}
```

### Placeholder During Load

```kotlin
@Composable
fun ThumbnailImage(url: String) {
    AsyncImage(
        model = url,
        contentDescription = null,
        placeholder = painterResource(R.drawable.placeholder),
        error = painterResource(R.drawable.error),
        modifier = Modifier.size(100.dp)
    )
}
```

## Remember Expensive Operations

### remember for Heavy Calculations

```kotlin
@Composable
fun ChartScreen(data: List<DataPoint>) {
    // BAD: Recalculates on every recomposition
    val chartData = processChartData(data)
    
    // GOOD: Only calculates when data changes
    val chartData = remember(data) {
        processChartData(data)
    }
    
    Chart(chartData)
}
```

### rememberSaveable for Configuration Changes

```kotlin
@Composable
fun SearchScreen() {
    // Survives configuration changes (rotation)
    var searchQuery by rememberSaveable { mutableStateOf("") }
    
    SearchBar(
        query = searchQuery,
        onQueryChange = { searchQuery = it }
    )
}
```

## Avoid Unnecessary Recomposition

### Stable Parameters

```kotlin
// BAD: Lambda causes recomposition
@Composable
fun Button(onClick: () -> Unit) {
    Button(onClick = onClick) {
        Text("Click")
    }
}

// GOOD: Stable lambda
@Composable
fun Button(onClick: () -> Unit) {
    val stableOnClick = rememberUpdatedState(onClick)
    Button(onClick = { stableOnClick.value() }) {
        Text("Click")
    }
}
```

### @Stable Annotation

```kotlin
@Stable
data class UserProfile(
    val name: String,
    val email: String,
    val avatarUrl: String
)

@Composable
fun ProfileCard(profile: UserProfile) {
    // Won't recompose unless profile actually changes
    Card {
        Text(profile.name)
        Text(profile.email)
    }
}
```

## Startup-Specific Patterns

### Skeleton Screens

```kotlin
@Composable
fun HomeScreen(viewModel: HomeViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    
    when (state) {
        is Loading -> {
            // Show skeleton immediately
            SkeletonHomeScreen()
        }
        is Success -> {
            RealHomeScreen(state.data)
        }
        is Error -> {
            ErrorScreen(state.message)
        }
    }
}

@Composable
fun SkeletonHomeScreen() {
    Column {
        repeat(5) {
            ShimmerBox(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(100.dp)
                    .padding(8.dp)
            )
        }
    }
}
```

### Progressive Loading

```kotlin
@Composable
fun FeedScreen(viewModel: FeedViewModel = hiltViewModel()) {
    val items = viewModel.pagingData.collectAsLazyPagingItems()
    
    LazyColumn {
        // Load first page immediately
        items(
            count = items.itemCount,
            key = { items[it]?.id ?: it }
        ) { index ->
            items[index]?.let { item ->
                FeedItem(item)
            } ?: FeedItemPlaceholder()
        }
        
        // Load more as user scrolls
        item {
            if (items.loadState.append is LoadState.Loading) {
                CircularProgressIndicator()
            }
        }
    }
}
```

## Measure Composition Performance

### Composition Tracing

```kotlin
@Composable
fun HomeScreen() {
    Trace.beginSection("HomeScreen.Composition")
    
    // Your composable content
    Column {
        TopBar()
        MainContent()
    }
    
    Trace.endSection()
}
```

### Recomposition Highlighter (Debug)

```kotlin
// In debug builds
@Composable
fun DebugRecompositionHighlighter() {
    if (BuildConfig.DEBUG) {
        val recompositions = remember { mutableStateOf(0) }
        
        SideEffect {
            recompositions.value++
        }
        
        Text(
            "Recompositions: ${recompositions.value}",
            modifier = Modifier
                .background(Color.Red.copy(alpha = 0.3f))
                .padding(4.dp)
        )
    }
}
```

## Common Pitfalls

### 1. Reading State Too Early

```kotlin
// BAD: Reads state in Composition
@Composable
fun AnimatedBox(offset: State<Int>) {
    Box(modifier = Modifier.offset(x = offset.value.dp))
}

// GOOD: Reads state in Layout
@Composable
fun AnimatedBox(offset: State<Int>) {
    Box(modifier = Modifier.offset { IntOffset(offset.value, 0) })
}
```

### 2. Unstable Parameters

```kotlin
// BAD: List is unstable
@Composable
fun ItemList(items: List<Item>) {
    items.forEach { ItemRow(it) }
}

// GOOD: Use ImmutableList
@Composable
fun ItemList(items: ImmutableList<Item>) {
    items.forEach { ItemRow(it) }
}
```

### 3. Heavy Work in Composition

```kotlin
// BAD: Heavy calculation on every recomposition
@Composable
fun ChartScreen(data: List<DataPoint>) {
    val processed = data.map { complexTransform(it) }
    Chart(processed)
}

// GOOD: Remember the result
@Composable
fun ChartScreen(data: List<DataPoint>) {
    val processed = remember(data) {
        data.map { complexTransform(it) }
    }
    Chart(processed)
}
```

## Best Practices Summary

1. **Defer composition** - Only compose what's visible
2. **Use derivedStateOf** - For expensive calculations
3. **Stable collections** - ImmutableList, persistentListOf
4. **Lambda modifiers** - Read state in later phases
5. **Key LazyColumn items** - Prevent unnecessary recomposition
6. **Async image loading** - Never block composition
7. **Remember expensive ops** - Cache calculations
8. **Skeleton screens** - Show UI immediately
9. **Progressive loading** - Load data incrementally
10. **Measure performance** - Use Composition tracing

## Integration with Baseline Profiles

Ensure Compose functions are in your Baseline Profile:

```text
# baseline-prof.txt
Lcom/example/myapp/ui/HomeScreenKt;->HomeScreen(Landroidx/compose/runtime/Composer;I)V
Lcom/example/myapp/ui/theme/ThemeKt;->AppTheme(ZLkotlin/jvm/functions/Function2;Landroidx/compose/runtime/Composer;II)V
Lcom/example/myapp/ui/components/TopBarKt;->TopBar(Landroidx/compose/runtime/Composer;I)V
```

This ensures Compose functions are AOT-compiled for faster initial composition.
