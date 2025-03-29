"""
업로드 및 분석 모듈
- YouTube Upload API를 사용하여 쇼츠 영상을 자동으로 업로드합니다.
- YouTube Analytics API를 사용하여 성과 지표를 수집하고 분석합니다.
- 제목, 설명, 해시태그를 자동으로 생성합니다.
"""
import os
import json
import logging
import time
from datetime import datetime, timedelta
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# 설정 파일 임포트
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    DATA_DIR, LOGS_DIR
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'youtube_uploader.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('youtube_uploader')

class YouTubeUploader:
    """YouTube 업로드 및 분석 클래스"""
    
    def __init__(self):
        """초기화 함수"""
        # 디렉토리 생성
        os.makedirs(os.path.join(DATA_DIR, 'analytics'), exist_ok=True)
        
        # OAuth 인증 설정
        self.credentials_file = os.path.join(DATA_DIR, 'credentials.json')
        self.token_file = os.path.join(DATA_DIR, 'token.json')
        
        # API 서비스
        self.youtube = None
        self.youtube_analytics = None
        
        logger.info("YouTubeUploader 초기화 완료")
    
    def authenticate(self):
        """
        YouTube API 인증
        
        Returns:
            bool: 인증 성공 여부
        """
        try:
            # 필요한 권한 범위
            scopes = [
                'https://www.googleapis.com/auth/youtube.upload',
                'https://www.googleapis.com/auth/youtube',
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/yt-analytics.readonly'
            ]
            
            credentials = None
            
            # 토큰 파일이 있으면 로드
            if os.path.exists(self.token_file):
                credentials = Credentials.from_authorized_user_info(
                    json.load(open(self.token_file)), scopes)
            
            # 토큰이 없거나 만료되었으면 새로 인증
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        logger.error(f"인증 파일이 없습니다: {self.credentials_file}")
                        logger.info("Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하고 credentials.json 파일을 다운로드하세요.")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, scopes)
                    credentials = flow.run_local_server(port=0)
                
                # 토큰 저장
                with open(self.token_file, 'w') as token:
                    token.write(credentials.to_json())
            
            # YouTube API 서비스 생성
            self.youtube = build('youtube', 'v3', credentials=credentials)
            
            # YouTube Analytics API 서비스 생성
            self.youtube_analytics = build('youtubeAnalytics', 'v2', credentials=credentials)
            
            logger.info("YouTube API 인증 성공")
            return True
            
        except Exception as e:
            logger.error(f"YouTube API 인증 실패: {e}")
            return False
    
    def upload_video(self, video_path, title, description, tags, category_id=22, privacy_status='public'):
        """
        YouTube에 영상 업로드
        
        Args:
            video_path (str): 업로드할 영상 파일 경로
            title (str): 영상 제목
            description (str): 영상 설명
            tags (list): 해시태그 목록
            category_id (int): 카테고리 ID (기본값: 22 - People & Blogs)
            privacy_status (str): 공개 상태 (public, unlisted, private)
            
        Returns:
            str: 업로드된 영상 ID
        """
        try:
            if not self.youtube:
                if not self.authenticate():
                    logger.error("YouTube API 인증이 필요합니다.")
                    return None
            
            # 영상 메타데이터
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': False
                }
            }
            
            # 미디어 파일 업로드
            media = MediaFileUpload(video_path, 
                                   chunksize=1024*1024, 
                                   resumable=True,
                                   mimetype='video/mp4')
            
            # 업로드 요청
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # 업로드 진행
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.info(f"업로드 진행 중: {int(status.progress() * 100)}%")
            
            # 업로드 완료
            video_id = response['id']
            logger.info(f"영상 업로드 완료: {video_id}")
            
            # 업로드 정보 저장
            upload_info = {
                'video_id': video_id,
                'title': title,
                'description': description,
                'tags': tags,
                'category_id': category_id,
                'privacy_status': privacy_status,
                'upload_time': datetime.now().isoformat()
            }
            
            upload_file = os.path.join(DATA_DIR, 'analytics', f"upload_{video_id}.json")
            with open(upload_file, 'w', encoding='utf-8') as f:
                json.dump(upload_info, f, ensure_ascii=False, indent=2)
            
            return video_id
            
        except HttpError as e:
            logger.error(f"영상 업로드 중 HTTP 오류 발생: {e.resp.status}, {e.content}")
            return None
        except Exception as e:
            logger.error(f"영상 업로드 중 오류 발생: {e}")
            return None
    
    def get_video_analytics(self, video_id, start_date=None, end_date=None, metrics=None):
        """
        영상 성과 지표 수집
        
        Args:
            video_id (str): YouTube 영상 ID
            start_date (str): 시작 날짜 (YYYY-MM-DD)
            end_date (str): 종료 날짜 (YYYY-MM-DD)
            metrics (list): 수집할 지표 목록
            
        Returns:
            dict: 성과 지표
        """
        try:
            if not self.youtube_analytics:
                if not self.authenticate():
                    logger.error("YouTube API 인증이 필요합니다.")
                    return None
            
            # 기본 지표
            if not metrics:
                metrics = [
                    'views', 'likes', 'dislikes', 'comments', 
                    'averageViewDuration', 'averageViewPercentage',
                    'subscribersGained', 'shares'
                ]
            
            # 날짜 설정
            if not end_date:
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            if not start_date:
                # 기본적으로 업로드 후 7일 데이터 수집
                start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # Analytics API 요청
            response = self.youtube_analytics.reports().query(
                ids=f'channel==MINE',
                startDate=start_date,
                endDate=end_date,
                metrics=','.join(metrics),
                dimensions='day',
                filters=f'video=={video_id}'
            ).execute()
            
            # 결과 처리
            analytics_data = {
                'video_id': video_id,
                'start_date': start_date,
                'end_date': end_date,
                'metrics': metrics,
                'data': response.get('rows', []),
                'column_headers': [h['name'] for h in response.get('columnHeaders', [])],
                'collection_time': datetime.now().isoformat()
            }
            
            # 결과 저장
            analytics_file = os.path.join(DATA_DIR, 'analytics', f"analytics_{video_id}_{start_date}_{end_date}.json")
            with open(analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"영상 성과 지표 수집 완료: {video_id}")
            return analytics_data
            
        except HttpError as e:
            logger.error(f"성과 지표 수집 중 HTTP 오류 발생: {e.resp.status}, {e.content}")
            return None
        except Exception as e:
            logger.error(f"성과 지표 수집 중 오류 발생: {e}")
            return None
    
    def get_video_comments(self, video_id, max_results=100):
        """
        영상 댓글 수집
        
        Args:
            video_id (str): YouTube 영상 ID
            max_results (int): 수집할 최대 댓글 수
            
        Returns:
            list: 댓글 목록
        """
        try:
            if not self.youtube:
                if not self.authenticate():
                    logger.error("YouTube API 인증이 필요합니다.")
                    return None
            
            # 댓글 스레드 요청
            comments = []
            next_page_token = None
            
            while len(comments) < max_results:
                # 댓글 스레드 요청
                response = self.youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    maxResults=min(100, max_results - len(comments)),
                    pageToken=next_page_token
                ).execute()
                
                # 댓글 추출
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'id': item['id'],
                        'author': comment['authorDisplayName'],
                        'text': comment['textDisplay'],
                        'like_count': comment['likeCount'],
                        'published_at': comment['publishedAt']
                    })
                
                # 다음 페이지 토큰
                next_page_token = response.get('nextPageToken')
                
                # 다음 페이지가 없으면 종료
                if not next_page_token:
                    break
            
            # 결과 저장
            comments_data = {
                'video_id': video_id,
                'comments': comments,
                'collection_time': datetime.now().isoformat()
            }
            
            comments_file = os.path.join(DATA_DIR, 'analytics', f"comments_{video_id}.json")
            with open(comments_file, 'w', encoding='utf-8') as f:
                json.dump(comments_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"영상 댓글 수집 완료: {video_id}, 댓글 수: {len(comments)}")
            return comments
            
        except HttpError as e:
            logger.error(f"댓글 수집 중 HTTP 오류 발생: {e.resp.status}, {e.content}")
            return None
        except Exception as e:
            logger.error(f"댓글 수집 중 오류 발생: {e}")
            return None
    
    def analyze_performance(self, video_id, periods=None):
        """
        영상 성과 분석
        
        Args:
            video_id (str): YouTube 영상 ID
            periods (list): 분석 기간 목록 (hours)
            
        Returns:
            dict: 성과 분석 결과
        """
        try:
            # 기본 분석 기간 (24시간, 72시간, 7일)
            if not periods:
                periods = [24, 72, 168]
            
            analysis_results = {}
            
            for hours in periods:
                # 시작 날짜 계산
                end_date = datetime.now()
                start_date = end_date - timedelta(hours=hours)
                
                # 날짜 형식 변환
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                # 성과 지표 수집
                analytics_data = self.get_video_analytics(
                    video_id, 
                    start_date=start_date_str, 
                    end_date=end_date_str
                )
                
                if not analytics_data:
                    continue
                
                # 댓글 수집 (첫 번째 기간에만)
                if hours == periods[0]:
                    comments = self.get_video_comments(video_id)
                
                # 분석 결과 저장
                period_key = f"{hours}h"
                analysis_results[period_key] = {
                    'analytics': analytics_data,
                    'summary': self._summarize_analytics(analytics_data)
                }
            
            # 전체 분석 결과
            result = {
                'video_id': video_id,
                'periods': analysis_results,
                'comments': comments if 'comments' in locals() else None,
                'analysis_time': datetime.now().isoformat()
            }
            
            # 결과 저장
            analysis_file = os.path.join(DATA_DIR, 'analytics', f"analysis_{video_id}.json")
            with open(analysis_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            logger.info(f"영상 성과 분석 완료: {video_id}")
            return result
            
        except Exception as e:
            logger.error(f"성과 분석 중 오류 발생: {e}")
            return None
    
    def _summarize_analytics(self, analytics_data):
        """
        성과 지표 요약
        
        Args:
            analytics_data (dict): 성과 지표 데이터
            
        Returns:
            dict: 요약 결과
        """
        try:
            # 데이터가 없으면 빈 요약 반환
            if not analytics_data or not analytics_data.get('data'):
                return {
                    'total_views': 0,
                    'total_likes': 0,
                    'total_comments': 0,
                    'avg_view_duration': 0,
                    'avg_view_percentage': 0,
                    'subscribers_gained': 0
                }
            
            # 컬럼 인덱스 찾기
            headers = analytics_data['column_headers']
            data = analytics_data['data']
            
            # 각 지표의 인덱스 찾기
            indices = {}
            for metric in ['views', 'likes', 'comments', 'averageViewDuration', 
                          'averageViewPercentage', 'subscribersGained']:
                try:
                    indices[metric] = headers.index(metric)
                except ValueError:
                    indices[metric] = None
            
            # 합계 계산
            total_views = sum(row[indices['views']] for row in data) if indices.get('views') is not None else 0
            total_likes = sum(row[indices['likes']] for row in data) if indices.get('likes') is not None else 0
            total_comments = sum(row[indices['comments']] for row in data) if indices.get('comments') is not None else 0
            subscribers_gained = sum(row[indices['subscribersGained']] for row in data) if indices.get('subscribersGained') is not None else 0
            
            # 평균 계산
            if indices.get('averageViewDuration') is not None and data:
                avg_view_duration = sum(row[indices['averageViewDuration']] for row in data) / len(data)
            else:
                avg_view_duration = 0
                
            if indices.get('averageViewPercentage') is not None and data:
                avg_view_percentage = sum(ro
(Content truncated due to size limit. Use line ranges to read in chunks)