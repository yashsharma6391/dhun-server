# from sqlalchemy.orm import Session
# from app.models.song import Song
# from app.models.channel import Channel
# from app.schemas.search import SearchResultResponse
# from app.services.song_service import song_to_response
# from app.services.channel_service import channel_to_response

# def search(query: str, db: Session) -> SearchResultResponse:
#     if not query or len(query.strip()) < 1:
#         return SearchResultResponse(songs=[], channels=[])
    
#     search_term = f"%{query.strip()}%"
    
#     # Search songs
#     songs = db.query(Song)\
#         .filter(
#             Song.is_active == True,
#             (
#                 Song.title.ilike(search_term) |
#                 Song.artist.ilike(search_term) |
#                 Song.album.ilike(search_term)
#             )
#         )\
#         .limit(20)\
#         .all()
    
#     # Search channels
#     channels = db.query(Channel)\
#         .filter(
#             Channel.is_public == True,
#             Channel.name.ilike(search_term)
#         )\
#         .limit(10)\
#         .all()
    
#     return SearchResultResponse(
#         songs=[song_to_response(s) for s in songs],
#         channels=[channel_to_response(c) for c in channels]
#     )