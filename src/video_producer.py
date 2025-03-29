"""
영상 제작 모듈
- ElevenLabs API를 사용하여 TTS(Text-to-Speech) 오디오를 생성합니다.
- FFmpeg를 사용하여 영상을 합성하고 자막을 삽입합니다.
- 쇼츠 형식에 최적화된 영상을 제작합니다.
"""
import os
import json
import logging
import tempfile
import subprocess
import requests
from datetime import datetime
import ffmpeg
import random
import time

# 설정 파일 임포트
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    ELEVENLABS_API_KEY, DATA_DIR, LOGS_DIR, TEMP_DIR, SHORTS_DURATION
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'video_producer.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('video_producer')

class VideoProducer:
    """영상 제작 클래스"""
    
    def __init__(self):
        """초기화 함수"""
        # 디렉토리 생성
        os.makedirs(os.path.join(DATA_DIR, 'audio'), exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'videos'), exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'output'), exist_ok=True)
        os.makedirs(TEMP_DIR, exist_ok=True)
        
        # FFmpeg 설치 확인
        self._check_ffmpeg()
        
        logger.info("VideoProducer 초기화 완료")
    
    def _check_ffmpeg(self):
        """FFmpeg 설치 확인 및 설치"""
        try:
            subprocess.run(['ffmpeg', '-version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("FFmpeg 설치 확인 완료")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("FFmpeg 설치 중...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            subprocess.run(['sudo', 'apt', 'install', '-y', 'ffmpeg'], check=True)
            logger.info("FFmpeg 설치 완료")
    
    def generate_tts_audio(self, text, voice_id="21m00Tcm4TlvDq8ikWAM", filename=None):
        """
        ElevenLabs API를 사용하여 TTS 오디오 생성
        
        Args:
            text (str): 변환할 텍스트
            voice_id (str): ElevenLabs 음성 ID
            filename (str): 저장할 파일 이름 (없으면 자동 생성)
            
        Returns:
            str: 생성된 오디오 파일 경로
        """
        try:
            if not ELEVENLABS_API_KEY:
                logger.error("ElevenLabs API 키가 설정되지 않았습니다.")
                return None
            
            # 파일 이름 생성
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"tts_{timestamp}.mp3"
            
            # 파일 경로
            audio_path = os.path.join(DATA_DIR, 'audio', filename)
            
            # API 요청
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                # 오디오 파일 저장
                with open(audio_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"TTS 오디오 생성 완료: {audio_path}")
                return audio_path
            else:
                logger.error(f"TTS 오디오 생성 실패: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"TTS 오디오 생성 중 오류 발생: {e}")
            return None
    
    def download_video(self, video_id, start_time=0, duration=SHORTS_DURATION):
        """
        YouTube 영상 다운로드
        
        Args:
            video_id (str): YouTube 영상 ID
            start_time (int): 시작 시간 (초)
            duration (int): 다운로드할 영상 길이 (초)
            
        Returns:
            str: 다운로드된 영상 파일 경로
        """
        try:
            # 파일 경로
            video_path = os.path.join(DATA_DIR, 'videos', f"{video_id}.mp4")
            
            # youtube-dl 또는 yt-dlp를 사용하여 영상 다운로드
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # yt-dlp 설치 확인 및 설치
            try:
                subprocess.run(['yt-dlp', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.info("yt-dlp 설치 중...")
                subprocess.run(['pip', 'install', 'yt-dlp'], check=True)
            
            # 영상 다운로드
            command = [
                'yt-dlp',
                '-f', 'bestvideo[height<=720]+bestaudio/best[height<=720]',
                '--merge-output-format', 'mp4',
                '-o', video_path,
                youtube_url
            ]
            
            subprocess.run(command, check=True)
            
            if os.path.exists(video_path):
                logger.info(f"영상 다운로드 완료: {video_id}")
                
                # 영상 자르기
                trimmed_video_path = os.path.join(DATA_DIR, 'videos', f"{video_id}_trimmed.mp4")
                
                # FFmpeg로 영상 자르기
                command = [
                    'ffmpeg',
                    '-i', video_path,
                    '-ss', str(start_time),
                    '-t', str(duration),
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    '-b:a', '192k',
                    trimmed_video_path
                ]
                
                subprocess.run(command, check=True)
                
                if os.path.exists(trimmed_video_path):
                    logger.info(f"영상 자르기 완료: {trimmed_video_path}")
                    return trimmed_video_path
                else:
                    logger.error(f"영상 자르기 실패: {video_id}")
                    return video_path
            else:
                logger.error(f"영상 다운로드 실패: {video_id}")
                return None
                
        except Exception as e:
            logger.error(f"영상 다운로드 중 오류 발생: {e}")
            return None
    
    def create_subtitle_file(self, script, output_path):
        """
        자막 파일 생성 (SRT 형식)
        
        Args:
            script (dict): 스크립트
            output_path (str): 저장할 파일 경로
            
        Returns:
            str: 생성된 자막 파일 경로
        """
        try:
            # 자막 내용 구성
            hook = script['hook']
            transition = script['transition']
            summary = script['summary']
            background = script['background']
            ending = script['ending']
            
            # 자막 타이밍 계산 (대략적인 추정)
            # 평균 말하기 속도 (초당 글자 수)
            chars_per_second = 4
            
            hook_duration = len(hook) / chars_per_second
            transition_duration = len(transition) / chars_per_second
            
            # 요약은 문장별로 분리
            summary_sentences = summary.split('. ')
            summary_sentences = [s + '.' for s in summary_sentences if s]
            
            # 자막 파일 내용
            srt_content = ""
            
            # 현재 시간 (밀리초)
            current_time = 0
            
            # Hook 자막
            srt_content += "1\n"
            srt_content += self._format_srt_time(current_time, current_time + hook_duration * 1000) + "\n"
            srt_content += hook + "\n\n"
            
            current_time += hook_duration * 1000
            
            # 전환 자막
            srt_content += "2\n"
            srt_content += self._format_srt_time(current_time, current_time + transition_duration * 1000) + "\n"
            srt_content += transition + "\n\n"
            
            current_time += transition_duration * 1000
            
            # 요약 자막 (문장별)
            for i, sentence in enumerate(summary_sentences):
                sentence_duration = len(sentence) / chars_per_second
                
                srt_content += f"{i+3}\n"
                srt_content += self._format_srt_time(current_time, current_time + sentence_duration * 1000) + "\n"
                srt_content += sentence + "\n\n"
                
                current_time += sentence_duration * 1000
            
            # 배경 자막
            background_duration = len(background) / chars_per_second
            
            srt_content += f"{len(summary_sentences)+3}\n"
            srt_content += self._format_srt_time(current_time, current_time + background_duration * 1000) + "\n"
            srt_content += background + "\n\n"
            
            current_time += background_duration * 1000
            
            # 마무리 자막
            ending_duration = len(ending) / chars_per_second
            
            srt_content += f"{len(summary_sentences)+4}\n"
            srt_content += self._format_srt_time(current_time, current_time + ending_duration * 1000) + "\n"
            srt_content += ending + "\n"
            
            # 자막 파일 저장
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"자막 파일 생성 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"자막 파일 생성 중 오류 발생: {e}")
            return None
    
    def _format_srt_time(self, start_ms, end_ms):
        """
        SRT 형식의 시간 문자열 생성
        
        Args:
            start_ms (int): 시작 시간 (밀리초)
            end_ms (int): 종료 시간 (밀리초)
            
        Returns:
            str: SRT 형식의 시간 문자열
        """
        def ms_to_srt(ms):
            seconds = ms // 1000
            ms = ms % 1000
            minutes = seconds // 60
            seconds = seconds % 60
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"
        
        return f"{ms_to_srt(start_ms)} --> {ms_to_srt(end_ms)}"
    
    def create_shorts_video(self, script, video_id):
        """
        쇼츠 영상 제작
        
        Args:
            script (dict): 스크립트
            video_id (str): YouTube 영상 ID
            
        Returns:
            str: 생성된 영상 파일 경로
        """
        try:
            # 1. 오디오 생성 (Hook 멘트)
            hook_audio_path = self.generate_tts_audio(script['hook'], filename=f"{video_id}_hook.mp3")
            
            if not hook_audio_path:
                logger.error(f"Hook 오디오 생성 실패: {video_id}")
                return None
            
            # 2. 영상 다운로드
            video_path = self.download_video(video_id)
            
            if not video_path:
                logger.error(f"영상 다운로드 실패: {video_id}")
                return None
            
            # 3. 자막 파일 생성
            subtitle_path = os.path.join(TEMP_DIR, f"{video_id}_subtitle.srt")
            self.create_subtitle_file(script, subtitle_path)
            
            # 4. 영상 합성
            output_path = os.path.join(DATA_DIR, 'output', f"{video_id}_shorts.mp4")
            
            # 영상 크기 조정 (9:16 비율)
            resized_video_path = os.path.join(TEMP_DIR, f"{video_id}_resized.mp4")
            
            # FFmpeg로 영상 크기 조정
            command = [
                'ffmpeg',
                '-i', video_path,
                '-vf', 'scale=-1:1920,crop=1080:1920',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-b:a', '192k',
                resized_video_path
            ]
            
            subprocess.run(command, check=True)
            
            # 자막 추가
            subtitled_video_path = os.path.join(TEMP_DIR, f"{video_id}_subtitled.mp4")
            
            # FFmpeg로 자막 추가
            command = [
                'ffmpeg',
                '-i', resized_video_path,
                '-vf', f"subtitles={subtitle_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H00000000,Bold=1,Alignment=10,MarginV=20'",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-b:a', '192k',
                subtitled_video_path
            ]
            
            subprocess.run(command, check=True)
            
            # Hook 오디오 추가
            # FFmpeg로 오디오 추가
            command = [
                'ffmpeg',
                '-i', subtitled_video_path,
                '-i', hook_audio_path,
                '-filter_complex', '[0:a]volume=0.3[a1];[1:a]adelay=0|0[a2];[a1][a2]amix=inputs=2:duration=first',
                '-c:v', 'copy',
                output_path
            ]
            
            subprocess.run(command, check=True)
            
            if os.path.exists(output_path):
                logger.info(f"쇼츠 영상 제작 완료: {output_path}")
                
                # 임시 파일 삭제
                for temp_file in [resized_video_path, subtitled_video_path, subtitle_path]:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                
                return output_path
            else:
                logger.error(f"쇼츠 영상 제작 실패: {video_id}")
                return None
                
        except Exception as e:
            logger.error(f"쇼츠 영상 제작 중 오류 발생: {e}")
            return None
    
    def create_preview_image(self, video_path, output_path=None):
        """
        미리보기 이미지 생성
        
        Args:
            video_path (str): 영상 파일 경로
            output_path (str): 저장할 파일 경로 (없으면 자동 생성)
            
        Returns:
            str: 생성된 이미지 파일 경로
        """
        try:
            # 파일 경로 생성
            if not output_path:
                video_name = os.path.basename(video_path).split('.')[0]
                output_path = os.path.join(DATA_DIR, 'output', f"{video_name}_preview.jpg")
            
            # FFmpeg로 미리보기 이미지 생성
            command = [
                'ffmpeg',
                '-i', video_path,
                '-ss', '00:00:01',
                '-vframes', '1',
                '-q:v', '2',
                output_path
            ]
            
            subprocess.run(command, check=True)
            
            if os.path.exists(output_path):
                logger.info(f"미리보기 이미지 생성 완료: {output_path}")
                return output_path
            else:
                logger.error(f"미리보기 이미지 생성 실패: {video_path}")
                return None
                
        except Exception as e:
            logger.error(f"미리보기 이미지 생성 중 오류 발생: {e}")
            return None

# 테스트 코드
if __name__ == "__main__":
    producer = VideoProducer()
    
    # 테스트용 스크립트
    script = {
        "hook": "세계 경제가 큰 위기에 직면했습니다?",
        "transition": "자세히 알아보겠습니다.",
        "summary": "미국 연방준비제도이사회가 기준금리를 0.5% 인상했습니다. 이는 지난 20년간 가장 큰 폭의 인상입니다. 전문가들은 인플레이션 억제를 위한 조치라고 분석합니다.",
        "background": "미국의 금리 인상은 전 세계 경제에 큰 영향을 미칠 것으로 예상됩니다.",
        "ending": "이상 글로벌 뉴스 단신이었습니다."
    }
    
    # 테스트용 영상 ID (실제 뉴스 영상 ID로 변경 필요)
    test_video_id = "dQw4w9WgXcQ"
    
    # 쇼츠 영상 제작
    output_path = producer.create_shorts_video(script, test_video_id)
    
    if output_path:
        print(f"쇼츠 영상 제작 완료: {output_path}")
        
        # 미리보기 이미지 생성
        preview_path = producer.create_preview_image(output_path)
        
        if preview_path:
            print(f"미리보기 이미지 생성 완료: {preview_path}")
    else:
        print("쇼츠 영상 제작 실패")
