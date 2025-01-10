# Local-Insight

1. Import following classes to frontend code.
```python
    from chat import OnlineChat, OfflineChat
    from retriever import RetrieverClient
```
2. Create a `RetrieverClient` object.
   
```python
    retriever = RetrieverClient(folder_path="...")
```
3. Create `OfflineChat` or `OnlineChat` object depending on mode.
```python
    chat = OfflineChat() if mode == "offline" else OnlineChat()
```
4. Get search results using `search()` method. If `text` or `image_path` not given then set them as `None`.
```python
    search_results = retriever.search(text="...", image_path=None)
```
5. To print response, modify following functions according to you need.
```python
    handle_offline_response(chat, user_text, ) if mode == "offline" else handle_online_response()
```
**go through bottom parts of `test_chat.ipynb` as well**