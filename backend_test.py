#!/usr/bin/env python3
"""
Backend API Testing for GCSE Question Bank Platform
Tests all core API endpoints using the public URL
"""

import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

class GCSEQuestionBankTester:
    def __init__(self, base_url="https://gcse-pdf-parser.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_paper_id = None
        self.session = requests.Session()
        self.session.timeout = 30

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int, 
                 data: Optional[Dict] = None, headers: Optional[Dict] = None) -> tuple[bool, Dict]:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        
        default_headers = {'Content-Type': 'application/json'}
        if headers:
            default_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=default_headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=default_headers)
            elif method == 'PATCH':
                response = self.session.patch(url, json=data, headers=default_headers)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                except:
                    response_data = {"raw_response": response.text}
                self.log_test(name, True, f"Status: {response.status_code}")
                return True, response_data
            else:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = f" - {error_data.get('detail', 'No detail')}"
                except:
                    error_detail = f" - {response.text[:100]}"
                
                self.log_test(name, False, f"Expected {expected_status}, got {response.status_code}{error_detail}")
                return False, {}

        except requests.exceptions.RequestException as e:
            self.log_test(name, False, f"Request error: {str(e)}")
            return False, {}
        except Exception as e:
            self.log_test(name, False, f"Unexpected error: {str(e)}")
            return False, {}

    def test_health_endpoint(self):
        """Test GET /api/health"""
        success, response = self.run_test(
            "Health Check",
            "GET", 
            "health",
            200
        )
        
        if success:
            if "status" in response and response["status"] == "healthy":
                print(f"   ✓ Health status: {response['status']}")
                print(f"   ✓ Storage initialized: {response.get('storage_initialized', 'unknown')}")
            else:
                print(f"   ⚠️  Unexpected health response: {response}")
        
        return success

    def test_root_endpoint(self):
        """Test GET /api/"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        
        if success:
            if "message" in response:
                print(f"   ✓ API Message: {response['message']}")
                print(f"   ✓ Version: {response.get('version', 'unknown')}")
            else:
                print(f"   ⚠️  Unexpected root response: {response}")
        
        return success

    def test_create_paper(self):
        """Test POST /api/papers"""
        paper_data = {
            "board": "AQA",
            "qualification": "GCSE", 
            "subject": "Mathematics",
            "paper_number": "1",
            "tier": "Higher",
            "session": "June",
            "exam_year": 2024
        }
        
        success, response = self.run_test(
            "Create Paper",
            "POST",
            "papers",
            200,
            data=paper_data
        )
        
        if success:
            if "id" in response:
                self.created_paper_id = response["id"]
                print(f"   ✓ Created paper ID: {self.created_paper_id}")
                print(f"   ✓ Board: {response.get('board')}")
                print(f"   ✓ Status: {response.get('status')}")
            else:
                print(f"   ⚠️  No paper ID in response: {response}")
        
        return success

    def test_list_papers(self):
        """Test GET /api/papers"""
        success, response = self.run_test(
            "List Papers",
            "GET",
            "papers", 
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✓ Found {len(response)} papers")
                if len(response) > 0:
                    print(f"   ✓ First paper: {response[0].get('board')} {response[0].get('exam_year')}")
            else:
                print(f"   ⚠️  Expected list, got: {type(response)}")
        
        return success

    def test_get_paper(self):
        """Test GET /api/papers/{paper_id}"""
        if not self.created_paper_id:
            print("❌ Get Paper - SKIPPED (no paper ID available)")
            return False
            
        success, response = self.run_test(
            "Get Paper by ID",
            "GET",
            f"papers/{self.created_paper_id}",
            200
        )
        
        if success:
            if "id" in response and response["id"] == self.created_paper_id:
                print(f"   ✓ Paper ID matches: {response['id']}")
                print(f"   ✓ Board: {response.get('board')}")
                print(f"   ✓ Total questions: {response.get('total_questions', 0)}")
            else:
                print(f"   ⚠️  Paper ID mismatch or missing: {response}")
        
        return success

    def test_get_stats(self):
        """Test GET /api/stats"""
        success, response = self.run_test(
            "Get Statistics",
            "GET",
            "stats",
            200
        )
        
        if success:
            expected_fields = ["total_papers", "total_questions", "approved_questions", "pending_review", "total_images"]
            missing_fields = [field for field in expected_fields if field not in response]
            
            if not missing_fields:
                print(f"   ✓ Total papers: {response['total_papers']}")
                print(f"   ✓ Total questions: {response['total_questions']}")
                print(f"   ✓ Approved questions: {response['approved_questions']}")
                print(f"   ✓ Pending review: {response['pending_review']}")
                print(f"   ✓ Total images: {response['total_images']}")
            else:
                print(f"   ⚠️  Missing fields: {missing_fields}")
        
        return success

    def test_list_questions(self):
        """Test GET /api/questions"""
        success, response = self.run_test(
            "List Questions",
            "GET",
            "questions",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✓ Found {len(response)} questions")
                if len(response) > 0:
                    q = response[0]
                    print(f"   ✓ First question: Q{q.get('question_number')} - {q.get('status')}")
            else:
                print(f"   ⚠️  Expected list, got: {type(response)}")
        
        return success

    def test_list_questions_with_filter(self):
        """Test GET /api/questions with paper_id filter"""
        if not self.created_paper_id:
            print("❌ List Questions (Filtered) - SKIPPED (no paper ID available)")
            return False
            
        success, response = self.run_test(
            "List Questions (Filtered by Paper)",
            "GET",
            f"questions?paper_id={self.created_paper_id}",
            200
        )
        
        if success:
            if isinstance(response, list):
                print(f"   ✓ Found {len(response)} questions for paper {self.created_paper_id}")
            else:
                print(f"   ⚠️  Expected list, got: {type(response)}")
        
        return success

    def test_invalid_endpoints(self):
        """Test some invalid endpoints to ensure proper error handling"""
        print("\n🔍 Testing Error Handling...")
        
        # Test 404 for non-existent paper
        success_404, _ = self.run_test(
            "Get Non-existent Paper",
            "GET",
            "papers/non-existent-id",
            404
        )
        
        # Test 404 for non-existent question  
        success_404_q, _ = self.run_test(
            "Get Non-existent Question",
            "GET", 
            "questions/non-existent-id",
            404
        )
        
        return success_404 and success_404_q

    def run_all_tests(self):
        """Run all backend API tests"""
        print("=" * 60)
        print("🚀 GCSE Question Bank Backend API Tests")
        print("=" * 60)
        print(f"Base URL: {self.base_url}")
        print(f"API URL: {self.api_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Core API tests
        tests = [
            self.test_health_endpoint,
            self.test_root_endpoint,
            self.test_get_stats,
            self.test_list_papers,
            self.test_list_questions,
            self.test_create_paper,
            self.test_get_paper,
            self.test_list_questions_with_filter,
            self.test_invalid_endpoints
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"❌ {test.__name__} - EXCEPTION: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "0%")
        
        if self.created_paper_id:
            print(f"\n📝 Created Paper ID: {self.created_paper_id}")
            print("   This paper can be used for frontend testing")
        
        return self.tests_passed == self.tests_run

def main():
    """Main test runner"""
    tester = GCSEQuestionBankTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())