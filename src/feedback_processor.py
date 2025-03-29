"""
피드백 및 강화학습 모듈
- 수집된 성과 데이터를 바탕으로 ChatGPT 기반 피드백을 생성합니다.
- 피드백을 기반으로 템플릿을 자동으로 수정합니다.
- 강화학습 이력을 데이터베이스에 저장하고 Notion API를 통해 리포트를 생성합니다.
"""
import os
import json
import logging
import time
from datetime import datetime, timedelta
import openai
import requests
import random
import sqlite3

# 설정 파일 임포트
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    OPENAI_API_KEY, DATA_DIR, LOGS_DIR
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'feedback_processor.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('feedback_processor')

# OpenAI API 키 설정
openai.api_key = OPENAI_API_KEY

class FeedbackProcessor:
    """피드백 및 강화학습 클래스"""
    
    def __init__(self, db_path=None):
        """
        초기화 함수
        
        Args:
            db_path (str): 데이터베이스 파일 경로
        """
        # 디렉토리 생성
        os.makedirs(os.path.join(DATA_DIR, 'feedback'), exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'reports'), exist_ok=True)
        
        # 데이터베이스 설정
        if not db_path:
            db_path = os.path.join(DATA_DIR, 'feedback.db')
        
        self.db_path = db_path
        self._init_database()
        
        # 템플릿 로드
        self.templates = self._load_templates()
        
        logger.info("FeedbackProcessor 초기화 완료")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 영상 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE,
                title TEXT,
                upload_time TEXT,
                hook_style TEXT,
                summary_length INTEGER,
                background_included BOOLEAN,
                subtitle_size TEXT,
                subtitle_speed TEXT,
                video_length INTEGER
            )
            ''')
            
            # 성과 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                period TEXT,
                views INTEGER,
                likes INTEGER,
                comments INTEGER,
                avg_view_duration REAL,
                avg_view_percentage REAL,
                collection_time TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
            ''')
            
            # 피드백 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                hook_feedback TEXT,
                summary_feedback TEXT,
                subtitle_feedback TEXT,
                length_feedback TEXT,
                overall_score INTEGER,
                generation_time TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
            ''')
            
            # 템플릿 변경 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS template_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                change_type TEXT,
                old_value TEXT,
                new_value TEXT,
                reason TEXT,
                change_time TEXT
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("데이터베이스 초기화 완료")
        except Exception as e:
            logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
    
    def _load_templates(self):
        """
        템플릿 로드
        
        Returns:
            dict: 템플릿 사전
        """
        template_file = os.path.join(DATA_DIR, 'templates.json')
        
        if os.path.exists(template_file):
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    templates = json.load(f)
                logger.info("템플릿 파일 로드 성공")
                return templates
            except Exception as e:
                logger.error(f"템플릿 파일 로드 실패: {e}")
                return self._get_default_templates()
        else:
            logger.warning("템플릿 파일이 없습니다. 기본 템플릿을 사용합니다.")
            return self._get_default_templates()
    
    def _get_default_templates(self):
        """
        기본 템플릿 반환
        
        Returns:
            dict: 기본 템플릿 사전
        """
        return {
            'hook': {
                'question': "{}?",
                'warning': "주의하세요! {}",
                'shocking': "충격! {}",
                'interesting': "놀라운 사실! {}"
            },
            'transition': [
                "자세히 알아보겠습니다.",
                "지금 바로 알려드립니다.",
                "함께 살펴보겠습니다.",
                "이것이 전체 내용입니다."
            ],
            'ending': [
                "이상 글로벌 뉴스 단신이었습니다.",
                "더 자세한 내용은 링크를 참고하세요.",
                "구독과 좋아요 부탁드립니다.",
                "다음 소식에서 다시 만나요."
            ]
        }
    
    def save_templates(self, templates):
        """
        템플릿 저장
        
        Args:
            templates (dict): 템플릿 사전
        """
        template_file = os.path.join(DATA_DIR, 'templates.json')
        
        try:
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            
            self.templates = templates
            logger.info("템플릿 파일 저장 완료")
        except Exception as e:
            logger.error(f"템플릿 파일 저장 실패: {e}")
    
    def store_video_metadata(self, video_id, title, script):
        """
        영상 메타데이터 저장
        
        Args:
            video_id (str): YouTube 영상 ID
            title (str): 영상 제목
            script (dict): 스크립트
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # Hook 스타일 추출
            hook = script['hook']
            hook_style = 'question' if hook.endswith('?') else \
                         'warning' if hook.startswith('주의') else \
                         'shocking' if hook.startswith('충격') else \
                         'interesting' if hook.startswith('놀라운') else \
                         'normal'
            
            # 요약 길이 계산
            summary_length = len(script['summary'].split())
            
            # 배경 설명 포함 여부
            background_included = bool(script.get('background', ''))
            
            # 자막 크기 및 속도 (기본값)
            subtitle_size = 'medium'
            subtitle_speed = 'normal'
            
            # 영상 길이 (기본값)
            video_length = 30
            
            # 데이터베이스에 저장
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO videos (
                video_id, title, upload_time, hook_style, summary_length,
                background_included, subtitle_size, subtitle_speed, video_length
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id, title, datetime.now().isoformat(), hook_style, summary_length,
                background_included, subtitle_size, subtitle_speed, video_length
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"영상 메타데이터 저장 완료: {video_id}")
            return True
        except Exception as e:
            logger.error(f"영상 메타데이터 저장 중 오류 발생: {e}")
            return False
    
    def store_performance_data(self, video_id, analytics_data):
        """
        성과 데이터 저장
        
        Args:
            video_id (str): YouTube 영상 ID
            analytics_data (dict): 성과 데이터
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 성과 데이터 추출
            periods = analytics_data.get('periods', {})
            
            # 데이터베이스에 저장
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for period, data in periods.items():
                summary = data.get('summary', {})
                
                cursor.execute('''
                INSERT INTO performance (
                    video_id, period, views, likes, comments,
                    avg_view_duration, avg_view_percentage, collection_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    video_id, period, summary.get('total_views', 0),
                    summary.get('total_likes', 0), summary.get('total_comments', 0),
                    summary.get('avg_view_duration', 0), summary.get('avg_view_percentage', 0),
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"성과 데이터 저장 완료: {video_id}")
            return True
        except Exception as e:
            logger.error(f"성과 데이터 저장 중 오류 발생: {e}")
            return False
    
    def generate_feedback(self, video_id, analytics_data, comments_data=None):
        """
        피드백 생성
        
        Args:
            video_id (str): YouTube 영상 ID
            analytics_data (dict): 성과 데이터
            comments_data (dict): 댓글 데이터
            
        Returns:
            dict: 생성된 피드백
        """
        try:
            # 영상 메타데이터 조회
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT title, hook_style, summary_length, background_included,
                   subtitle_size, subtitle_speed, video_length
            FROM videos
            WHERE video_id = ?
            ''', (video_id,))
            
            video_data = cursor.fetchone()
            conn.close()
            
            if not video_data:
                logger.error(f"영상 메타데이터를 찾을 수 없음: {video_id}")
                return None
            
            title, hook_style, summary_length, background_included, \
            subtitle_size, subtitle_speed, video_length = video_data
            
            # 성과 데이터 추출
            periods = analytics_data.get('periods', {})
            
            # 가장 긴 기간의 성과 데이터 사용
            longest_period = max(periods.keys()) if periods else None
            performance = periods.get(longest_period, {}).get('summary', {}) if longest_period else {}
            
            # 댓글 데이터 추출
            comments = comments_data.get('comments', []) if comments_data else []
            comment_texts = [comment.get('text', '') for comment in comments]
            
            # OpenAI API를 사용하여 피드백 생성
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert YouTube Shorts analytics consultant specializing in optimizing content for maximum engagement."},
                    {"role": "user", "content": f"""
                    다음 YouTube Shorts 영상의 성과 데이터를 분석하고 피드백을 제공해주세요.
                    
                    영상 정보:
                    - 제목: {title}
                    - Hook 스타일: {hook_style}
                    - 요약 길이: {summary_length} 단어
                    - 배경 설명 포함 여부: {'포함' if background_included else '미포함'}
                    - 자막 크기: {subtitle_size}
                    - 자막 속도: {subtitle_speed}
                    - 영상 길이: {video_length}초
                    
                    성과 데이터:
                    - 조회수: {performance.get('total_views', 0)}
                    - 좋아요: {performance.get('total_likes', 0)}
                    - 댓글 수: {performance.get('total_comments', 0)}
                    - 평균 시청 시간: {performance.get('avg_view_duration', 0):.1f}초
                    - 평균 시청 비율: {performance.get('avg_view_percentage', 0):.1f}%
                    
                    댓글 (최대 10개):
                    {chr(10).join(comment_texts[:10]) if comment_texts else '댓글 없음'}
                    
                    다음 항목에 대한 피드백과 개선 방안을 JSON 형식으로 제공해주세요:
                    1. Hook 멘트 (스타일, 길이, 효과성)
                    2. 요약 내용 (길이, 명확성, 흥미도)
                    3. 자막 (크기, 속도, 가독성)
                    4. 영상 길이 (최적 길이 제안)
                    5. 종합 점수 (1-10점)
                    
                    다음 형식으로 응답해주세요:
                    {{
                        "hook_feedback": "Hook 멘트에 대한 피드백",
                        "summary_feedback": "요약 내용에 대한 피드백",
                        "subtitle_feedback": "자막에 대한 피드백",
                        "length_feedback": "영상 길이에 대한 피드백",
                        "overall_score": 점수,
                        "improvement_suggestions": [
                            "개선 제안 1",
                            "개선 제안 2",
                            "개선 제안 3"
                        ]
                    }}
                    """
                    }
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            feedback = json.loads(response.choices[0].message.content)
            
            # 피드백 저장
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO feedback (
                video_id, hook_feedback, summary_feedback, subtitle_feedback,
                length_feedback, overall_score, generation_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_id, feedback.get('hook_feedback', ''),
                feedback.get('summary_feedback', ''),
                feedback.get('subtitle_feedback', ''),
                feedback.get('length_feedback', ''),
                feedback.get('overall_score', 0),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            # 피드백 파일 저장
            feedback_file = os.path.join(DATA_DIR, 'feedback', f"feedback_{video_id}.json")
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback, f, ensure_ascii=False, indent=2)
            
            logger.info(f"피드백 생성 완료: {video_id}")
            return feedback
        except Exception as e:
            logger.error(f"피드백 생성 중 오류 발생: {e}")
            return None
    
    def update_templates_based_on_feedback(self, feedback_list):
        """
        피드백 기반 템플릿 업데이트
        
        Args:
            feedback_list (list): 피드백 목록
            
        Returns:
            dict: 업데이트된 템플릿
        """
        try:
            # 피드백이 충분하지 않으면 업데이트하지 않음
            if len(feedback_list) < 3:
                logger.info("피드백이 충분하지 않아 템플릿을 업데이트하지 않습니다.")
                return self.templates
            
            # 피드백 분석
            hook_feedbacks = [f.get('hook_feedback', '') for f in feedback_list]
            summary_feedbacks = [f.get('summary_feedback', '') for f in feedback_list]
            subtitle_feedbacks = [f.get('subtitle_feedback', '') for f in feedback_list]
            length_feedbacks = [f.get('length_feedback', '') for f in feedback_list]
            
            # OpenAI API를 사용하여 템플릿 업데이트 제안 생성
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert in content optimization and template design for short-form videos."},
                    {"role": "user", "content": f"""
                    다음은 YouTube Shorts 영상에 대한 여러 피드백입니다. 이를 바탕으로 템플릿 업데이트 제안을 해주세요.
                    
                    현재 템플릿:
                    {json.dumps(self.templates, ensure_ascii=False, indent=2)}
                    
                   
(Content truncated due to size limit. Use line ranges to read in chunks)