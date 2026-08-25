# -*- coding: utf-8 -*-
"""
اختبارات قاعدة البيانات
"""

import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# إضافة المسار الرئيسي
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager import DatabaseManager, Database, VideoDatabase, PlatformDatabase
from database.models import Video, Platform, Analytics
from database.maintenance import DatabaseMaintenance, DatabaseReports


@pytest.fixture
def temp_db(tmp_path):
    """إنشاء قاعدة بيانات مؤقتة"""
    db_path = str(tmp_path / 'test.db')
    manager = DatabaseManager(db_path)
    yield manager
    # التنظيف
    if Path(db_path).exists():
        Path(db_path).unlink()


@pytest.fixture
def sample_video_data():
    """بيانات فيديو عينة"""
    return {
        'filename': 'test_video.mp4',
        'file_path': '/path/to/test.mp4',
        'title': 'فيديو اختبار',
        'description': 'وصف الفيديو',
        'duration': 120,
        'size': 1024000,
        'format': 'mp4',
        'resolution': '1080p'
    }


class TestDatabase:
    """اختبارات قاعدة البيانات الأساسية"""
    
    def test_database_initialization(self, temp_db):
        """اختبار تهيئة قاعدة البيانات"""
        assert temp_db is not None
        assert Path(temp_db.db.db_path).exists()
    
    def test_connection_context_manager(self, temp_db):
        """اختبار إدارة الاتصال"""
        with temp_db.db.get_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = cursor.fetchall()
            assert len(tables) > 0


class TestVideoDatabase:
    """اختبارات قاعدة بيانات الفيديوهات"""
    
    def test_add_video(self, temp_db, sample_video_data):
        """اختبار إضافة فيديو"""
        video_id = temp_db.videos.add_video(sample_video_data)
        assert video_id > 0
    
    def test_get_video(self, temp_db, sample_video_data):
        """اختبار الحصول على فيديو"""
        video_id = temp_db.videos.add_video(sample_video_data)
        video = temp_db.videos.get_video(video_id)
        
        assert video is not None
        assert video['title'] == 'فيديو اختبار'
        assert video['filename'] == 'test_video.mp4'
    
    def test_update_video(self, temp_db, sample_video_data):
        """اختبار تحديث الفيديو"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        result = temp_db.videos.update_video(video_id, {
            'title': 'عنوان جديد',
            'status': 'processed'
        })
        
        assert result is True
        video = temp_db.videos.get_video(video_id)
        assert video['title'] == 'عنوان جديد'
        assert video['status'] == 'processed'
    
    def test_get_all_videos(self, temp_db, sample_video_data):
        """اختبار الحصول على جميع الفيديوهات"""
        # إضافة عدة فيديوهات
        for i in range(3):
            data = sample_video_data.copy()
            data['filename'] = f'video_{i}.mp4'
            temp_db.videos.add_video(data)
        
        videos = temp_db.videos.get_all_videos()
        assert len(videos) >= 3
    
    def test_delete_video(self, temp_db, sample_video_data):
        """اختبار حذف فيديو"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        result = temp_db.videos.delete_video(video_id)
        assert result is True
        
        video = temp_db.videos.get_video(video_id)
        assert video is None
    
    def test_duplicate_filename_error(self, temp_db, sample_video_data):
        """اختبار خطأ اسم ملف مكرر"""
        temp_db.videos.add_video(sample_video_data)
        
        # محاولة إضافة نفس الملف
        result = temp_db.videos.add_video(sample_video_data)
        assert result == -1


class TestPlatformDatabase:
    """اختبارات قاعدة بيانات المنصات"""
    
    def test_add_platform_upload(self, temp_db, sample_video_data):
        """اختبار إضافة رفع منصة"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        result = temp_db.platforms.add_platform_upload(
            video_id,
            'youtube',
            {
                'platform_id': 'yt_123',
                'upload_url': 'https://youtube.com/watch?v=123'
            }
        )
        
        assert result is True
    
    def test_get_platform_stats(self, temp_db, sample_video_data):
        """اختبار الحصول على إحصائيات المنصة"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        temp_db.platforms.add_platform_upload(
            video_id,
            'youtube',
            {'platform_id': 'yt_123', 'upload_url': 'https://youtube.com'}
        )
        
        stats = temp_db.platforms.get_platform_stats(video_id, 'youtube')
        assert stats is not None
        assert stats['platform_name'] == 'youtube'
    
    def test_update_platform_stats(self, temp_db, sample_video_data):
        """اختبار تحديث إحصائيات المنصة"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        temp_db.platforms.add_platform_upload(
            video_id,
            'youtube',
            {'platform_id': 'yt_123', 'upload_url': 'https://youtube.com'}
        )
        
        result = temp_db.platforms.update_platform_stats(
            video_id,
            'youtube',
            {
                'view_count': 1000,
                'like_count': 50,
                'comment_count': 10,
                'share_count': 5
            }
        )
        
        assert result is True
        stats = temp_db.platforms.get_platform_stats(video_id, 'youtube')
        assert stats['view_count'] == 1000


class TestAnalyticsDatabase:
    """اختبارات قاعدة بيانات التحليلات"""
    
    def test_add_analytics(self, temp_db, sample_video_data):
        """اختبار إضافة بيانات تحليلية"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        result = temp_db.analytics.add_analytics(
            video_id,
            'youtube',
            {
                'views': 1000,
                'engagement_rate': 0.05,
                'watch_time': 5000,
                'reach': 2000,
                'impressions': 3000
            }
        )
        
        assert result is True
    
    def test_get_analytics(self, temp_db, sample_video_data):
        """اختبار الحصول على التحليلات"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        temp_db.analytics.add_analytics(video_id, 'youtube', {
            'views': 1000,
            'engagement_rate': 0.05
        })
        
        analytics = temp_db.analytics.get_analytics(video_id)
        assert len(analytics) > 0
        assert analytics[0]['views'] == 1000


class TestLogDatabase:
    """اختبارات قاعدة بيانات السجلات"""
    
    def test_add_log(self, temp_db, sample_video_data):
        """اختبار إضافة سجل"""
        video_id = temp_db.videos.add_video(sample_video_data)
        
        result = temp_db.logs.add_log(
            'info',
            'تم معالجة الفيديو',
            video_id=video_id,
            details='تم المعالجة بنجاح'
        )
        
        assert result is True
    
    def test_get_logs(self, temp_db):
        """اختبار الحصول على السجلات"""
        temp_db.logs.add_log('info', 'رسالة اختبار')
        temp_db.logs.add_log('error', 'خطأ اختبار')
        
        logs = temp_db.logs.get_logs(limit=10)
        assert len(logs) >= 2


class TestDatabaseMaintenance:
    """اختبارات صيانة قاعدة البيانات"""
    
    def test_database_stats(self, temp_db, sample_video_data):
        """اختبار إحصائيات قاعدة البيانات"""
        # إضافة بيانات
        temp_db.videos.add_video(sample_video_data)
        temp_db.logs.add_log('info', 'رسالة')
        
        maintenance = DatabaseMaintenance(temp_db)
        stats = maintenance.get_database_stats()
        
        assert 'videos_count' in stats
        assert 'logs_count' in stats
        assert 'database_size_mb' in stats
    
    def test_optimize_database(self, temp_db):
        """اختبار تحسين قاعدة البيانات"""
        maintenance = DatabaseMaintenance(temp_db)
        result = maintenance.optimize_database()
        
        assert result is True
    
    def test_backup_database(self, temp_db, tmp_path):
        """اختبار النسخ الاحتياطي"""
        backup_path = str(tmp_path / 'backup.db')
        
        maintenance = DatabaseMaintenance(temp_db)
        result = maintenance.backup_database(backup_path)
        
        assert result is True
        assert Path(backup_path).exists()


class TestDatabaseModels:
    """اختبارات نماذج البيانات"""
    
    def test_video_model(self):
        """اختبار نموذج الفيديو"""
        video = Video(
            filename='test.mp4',
            file_path='/path/to/test.mp4',
            title='اختبار',
            duration=120
        )
        
        data = video.to_dict()
        assert data['filename'] == 'test.mp4'
        assert data['title'] == 'اختبار'
    
    def test_platform_model(self):
        """اختبار نموذج المنصة"""
        platform = Platform(
            video_id=1,
            platform_name='youtube',
            view_count=100,
            like_count=10
        )
        
        data = platform.to_dict()
        assert data['platform_name'] == 'youtube'
        assert data['view_count'] == 100


class TestDatabaseReports:
    """اختبارات تقارير قاعدة البيانات"""
    
    def test_performance_report(self, temp_db, sample_video_data):
        """اختبار تقرير الأداء"""
        temp_db.videos.add_video(sample_video_data)
        
        reports = DatabaseReports(temp_db)
        report = reports.get_performance_report()
        
        assert 'dashboard' in report
        assert 'videos_by_status' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
