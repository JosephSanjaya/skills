# Store5 & Storage Code Samples

Practical implementation patterns.

## 1. Store5 Features

### Fetcher (of, ofResult, ofFlow)
```kotlin
// 1. Fetcher.of (Standard)
val fetcher = Fetcher.of { id: String -> api.getPost(id) }

// 2. Fetcher.ofResult (Exceptions bypassed)
val fetcherResult = Fetcher.ofResult { id: String ->
    try {
        FetcherResult.Data(api.getPost(id))
    } catch (e: Exception) {
        FetcherResult.Error.Custom(e)
    }
}

// 3. Fetcher.ofFlow (Streaming/Paging)
val fetcherFlow = Fetcher.ofFlow { query: Query ->
    flow {
        val page1 = api.getPosts(query.page)
        emit(page1)
    }
}
```

### SourceOfTruth (Room/SQLDelight Flow)
```kotlin
val sot = SourceOfTruth.of<String, PostDto, Post>(
    reader = { id -> dao.observePost(id) }, // Flow<Post?>
    writer = { id, dto -> dao.upsert(dto.toEntity()) }
)
```

### Converter (Type Mapping)
```kotlin
val converter = Converter.Builder<PostDto, PostEntity, Post>()
    .fromNetworkToLocal { dto -> PostEntity(dto.id, dto.title) }
    .fromOutputToLocal { post -> PostEntity(post.id, post.title) }
    .build()
```

### Validator (TTL with Jitter)
```kotlin
val validator = Validator.by<Post> { post ->
    val jitter = (0..20).random() / 100.0 // 0-20%
    val ttl = 10.minutes * (1.0 + jitter)
    post.cachedAt + ttl.inWholeMilliseconds > System.currentTimeMillis()
}
```

### Updater & Bookkeeper (MutableStore)
```kotlin
val updater = Updater.by<String, Post, PostWriteResponse>(
    post = { id, post ->
        val res = api.updatePost(id, post.toDto())
        if (res.isSuccessful) UpdaterResult.Success.Typed(res.body()!!)
        else UpdaterResult.Error.Message("HTTP ${res.code()}")
    }
)

val bookkeeper = Bookkeeper.by<String>(
    getLastFailedSync = { id -> prefs.getLong(id, -1L).takeIf { it >= 0 } },
    setLastFailedSync = { id, ts -> prefs.putLong(id, ts); true },
    clear = { id -> prefs.remove(id); true },
    clearAll = { prefs.clear(); true }
)
```

---

## 2. Memory Cache Configuration
```kotlin
val memoryPolicy = MemoryPolicy.builder<String, Post>()
    .setExpireAfterWrite(15.minutes) // Or setExpireAfterAccess(15.minutes)
    .setMaxSize(500)
    .build()
```

---

## 3. Key-Value Storage (DataStore SourceOfTruth)
```kotlin
class DataStoreSoT(private val dataStore: DataStore<Preferences>) {
    fun create(): SourceOfTruth<String, SettingsDto, Settings> = SourceOfTruth.of(
        reader = { key ->
            dataStore.data.map { prefs ->
                prefs[stringPreferencesKey(key)]?.toSettings()
            }
        },
        writer = { key, dto ->
            dataStore.edit { prefs ->
                prefs[stringPreferencesKey(key)] = dto.toJsonString()
            }
        }
    )
}
```

---

## 4. Complex Database (Room SourceOfTruth)

### Entity & DAO
```kotlin
@Entity(tableName = "posts")
data class PostEntity(
    @PrimaryKey val id: String,
    val title: String,
    val cachedAt: Long = System.currentTimeMillis()
)

@Dao
interface PostDao {
    @Query("SELECT * FROM posts WHERE id = :id")
    fun observePost(id: String): Flow<PostEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(entity: PostEntity)
}
```

### SoT Integration
```kotlin
class RoomSourceOfTruthFactory(private val dao: PostDao) {
    fun create(): SourceOfTruth<String, PostDto, Post> = SourceOfTruth.of(
        reader = { id ->
            dao.observePost(id).map { entity ->
                entity?.let { Post(it.id, it.title, it.cachedAt) }
            }
        },
        writer = { _, dto ->
            dao.upsert(PostEntity(dto.id, dto.title))
        }
    )
}
```
