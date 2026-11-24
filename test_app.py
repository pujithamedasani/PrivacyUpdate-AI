import json
import unittest
from app import create_app
from database import query_db, get_direct_db
from seed import seed_database

class PrivacyUpdateAITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_database_tables_exist(self):
        """Verify all 11 required tables exist and have seed data."""
        tables = [
            'project_details', 'team_members', 'milestones', 'tasks',
            'sources', 'snapshots', 'changes', 'reviews', 'scan_logs',
            'resources', 'deliverables'
        ]
        conn = get_direct_db()
        cursor = conn.cursor()
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0, f"Table {t} should contain seed records.")
        conn.close()

    def test_02_all_html_pages_render_200(self):
        """Verify every single HTML page renders properly with HTTP 200."""
        endpoints = [
            '/',
            '/project',
            '/sources',
            '/snapshots',
            '/changes',
            '/reviews',
            '/team',
            '/deliverables',
            '/resources',
            '/reports'
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Endpoint {ep} failed with {res.status_code}")
            self.assertIn(b"PrivacyUpdate", res.data, f"Endpoint {ep} should include brand title")

    def test_03_dashboard_stats_api(self):
        """Verify dashboard statistics API returns correct dynamic JSON."""
        res = self.client.get('/api/dashboard/stats')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['summary']['total_sources'], 0)
        self.assertGreater(data['summary']['total_snapshots'], 0)
        self.assertIn('categories_distribution', data)
        self.assertIn('reviews_distribution', data)
        self.assertIn('severity_distribution', data)
        self.assertIn('source_changes', data)

    def test_04_project_details_api(self):
        """Verify project details can be fetched and updated in database."""
        res = self.client.get('/api/project')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['project']['title'], "PrivacyUpdate AI")

        # Test updating project title
        put_res = self.client.put('/api/project', json={
            "title": "PrivacyUpdate AI (Academic Edition)",
            "description": data['project']['description'],
            "problem_statement": data['project']['problem_statement'],
            "proposed_solution": data['project']['proposed_solution'],
            "objectives": data['project']['objectives'],
            "scope": data['project']['scope'],
            "technologies": data['project']['technologies']
        })
        self.assertEqual(put_res.status_code, 200)

        # Verify persisted
        check_res = self.client.get('/api/project')
        self.assertEqual(check_res.get_json()['project']['title'], "PrivacyUpdate AI (Academic Edition)")

        # Revert to standard title
        self.client.put('/api/project', json={
            "title": "PrivacyUpdate AI",
            "description": data['project']['description'],
            "problem_statement": data['project']['problem_statement'],
            "proposed_solution": data['project']['proposed_solution'],
            "objectives": data['project']['objectives'],
            "scope": data['project']['scope'],
            "technologies": data['project']['technologies']
        })

    def test_05_sources_crud(self):
        """Verify adding, editing, toggling, and deleting a monitored source."""
        # Add source
        add_res = self.client.post('/api/sources', json={
            "name": "Test Service Terms",
            "url": "https://testservice.example.org/privacy",
            "description": "Integration test monitored source",
            "is_active": True
        })
        self.assertEqual(add_res.status_code, 200)
        source_id = add_res.get_json()['source_id']

        # Edit source
        edit_res = self.client.put(f'/api/sources/{source_id}', json={
            "name": "Test Service Terms Updated",
            "url": "https://testservice.example.org/privacy",
            "description": "Updated description",
            "is_active": True
        })
        self.assertEqual(edit_res.status_code, 200)

        # Toggle source
        tog_res = self.client.post(f'/api/sources/{source_id}/toggle')
        self.assertEqual(tog_res.status_code, 200)
        self.assertEqual(tog_res.get_json()['is_active'], 0)

        # Delete source
        del_res = self.client.delete(f'/api/sources/{source_id}')
        self.assertEqual(del_res.status_code, 200)

    def test_06_snapshot_comparison(self):
        """Verify snapshot comparison returns similarity and diff hunks."""
        res = self.client.get('/api/snapshots/compare?old_id=1&new_id=2')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(data['similarity'], 0.0)
        self.assertGreater(data['diff_count'], 0)

    def test_07_human_review_workflow(self):
        """Verify submitting human review decision updates change review status."""
        res = self.client.post('/api/reviews/submit', json={
            "change_id": 3,
            "reviewer_id": 1,
            "reviewer_name": "Pujitha Medasani",
            "decision": "Approved",
            "comments": "Automated test verification approved."
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['decision'], "Approved")

        # Verify change status updated in DB
        with self.app.app_context():
            ch = query_db("SELECT review_status FROM changes WHERE id = 3", one=True)
            self.assertEqual(ch['review_status'], "Approved")

    def test_08_reports_summary_analytics(self):
        """Verify reports summary API returns correct analytics and source coverage."""
        res = self.client.get('/api/reports/summary')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('severities', data)
        self.assertIn('categories', data)
        self.assertIn('sources_summary', data)

    def test_09_team_member_crud(self):
        """Verify team member add, edit, and delete."""
        add_res = self.client.post('/api/team', json={
            "name": "Jordan Lee",
            "reg_number": "CS-2025-099",
            "role": "QA Verification Specialist",
            "email": "jordan.lee@univ.edu",
            "responsibilities": "Unit testing and audit verification"
        })
        self.assertEqual(add_res.status_code, 200)
        member_id = add_res.get_json()['member_id']

        del_res = self.client.delete(f'/api/team/{member_id}')
        self.assertEqual(del_res.status_code, 200)

    def test_10_deliverables_and_reports_export(self):
        """Verify reports export CSV, JSON, and DB backup."""
        csv_res = self.client.get('/api/reports/export/changes')
        self.assertEqual(csv_res.status_code, 200)
        self.assertIn(b"Change ID,Website Name", csv_res.data)

        json_res = self.client.get('/api/reports/export/json')
        self.assertEqual(json_res.status_code, 200)
        json_data = json.loads(json_res.data)
        self.assertIn("monitored_sources", json_data)

        backup_res = self.client.get('/api/backup')
        self.assertEqual(backup_res.status_code, 200)
        backup_res.close()

if __name__ == '__main__':
    unittest.main()
