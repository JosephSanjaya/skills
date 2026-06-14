# Store5 Code Samples

## StoreBuilder (Read-Only)

```kotlin
import org.mobilenativefoundation.store.store5.*
import kotlin.time.Duration.Companion.minutes

val store: Store<String, Post> = StoreBuilder
    .from(
        fetcher = Fetcher.of { id -> api.getPost(id) },
        sourceOfTruth = SourceOfTruth.of(
            reader = { id -> dao.observePost(id) }, // Flow<PostEntity?>
            writer = { id, entity -> dao.upsert(entity) }
        )
    )
    .cachePolicy(
        MemoryPolicy.builder<String, Post>()
            .setExpireAfterWrite(10.minutes)
            .setMaxSize(200)
            .build()
    )
    .build()
```

## MutableStoreBuilder (Write Sync)

```kotlin
import org.mobilenativefoundation.store.store5.*
import org.mobilenativefoundation.store.core5.ExperimentalStoreApi

@OptIn(ExperimentalStoreApi::class)
val mutableStore: MutableStore<String, Post> = MutableStoreBuilder
    .from(
        fetcher = Fetcher.of { id -> api.getPost(id) },
        sourceOfTruth = SourceOfTruth.of(
            reader = { id -> dao.observePost(id) },
            writer = { id, entity -> dao.upsert(entity) }
        ),
        converter = Converter.Builder<PostDto, PostEntity, Post>()
            .fromNetworkToLocal { dto -> PostEntity(dto.id, dto.title) }
            .fromOutputToLocal { post -> PostEntity(post.id, post.title) }
            .build()
    )
    .build(
        updater = Updater.by(
            post = { key, post ->
                val res = api.updatePost(key, post.toDto())
                if (res.isSuccessful) UpdaterResult.Success.Typed(res.body()!!)
                else UpdaterResult.Error.Message("HTTP ${res.code()}")
            }
        ),
        bookkeeper = Bookkeeper.by(
            getLastFailedSync = { key -> prefs.getLong(key, -1L).takeIf { it >= 0 } },
            setLastFailedSync = { key, ts -> prefs.putLong(key, ts); true },
            clear = { key -> prefs.remove(key); true },
            clearAll = { prefs.clear(); true }
        )
    )
```

## Repository Layer Integration

```kotlin
interface PostRepository {
    fun observePost(id: String): Flow<Post>
    suspend fun updatePost(post: Post): Boolean
}

class RealPostRepository(private val store: MutableStore<String, Post>) : PostRepository {
    override fun observePost(id: String): Flow<Post> =
        store.stream(StoreReadRequest.cached(id, refresh = true))
            .filterIsInstance<StoreReadResponse.Data<Post>>()
            .map { it.value }

    override suspend fun updatePost(post: Post): Boolean {
        val request = StoreWriteRequest.of<String, Post, PostWriteResponse>(post.id, post)
        return when (store.write(request)) {
            is StoreWriteResponse.Success -> true
            is StoreWriteResponse.Error -> false
        }
    }
}
```
