import { BrowserRouter, Route, Routes, useLocation, useParams } from "react-router-dom";
import Home from "./pages/Home";
import ProtectedRoute from "./components/ProtectedRoute";
import Sidebar from "./components/Sidebar";

import "./App.css";
import Profile from "./pages/Profile";
import CreateClass from "./pages/CreateClass";
import LoginPage from "./pages/LoginPage";
import ClassHome from "./pages/ClassHome";
import ClassMembers from "./pages/ClassMembers";
import Assignment from "./pages/Assignment";
import Group from "./pages/Group";
import RegisterPage from "./pages/RegisterPage";
import ChangePassword from "./pages/ChangePassword";
import CreateTeacher from "./pages/CreateTeacher";
import ReviewHistoryPage from "./pages/ReviewHistoryPage";
import TeacherReviewsPage from "./pages/TeacherReviewsPage";
import AdminUsersPage from "./pages/AdminUsersPage";
import AssignmentAnalytics from "./pages/AssignmentAnalytics";
import ActivityFeedPage from "./pages/ActivityFeedPage";
import RubricBuilderPage from "./pages/RubricBuilderPage";
import FeedbackView from "./pages/FeedbackView";
import StudentProgressPage from './pages/StudentProgressPage';
import TeamSubmissionsPanel from './components/TeamSubmissionsPanel';

function TeamSubmissionsRoute() {
  const { id } = useParams<{ id: string }>();
  return <TeamSubmissionsPanel assignmentId={Number(id)} />;
}

function AppContent() {
  const location = useLocation();
  const noSidebarPaths = ["/", "/login", "/register", "/change-password"];

  return (
    <div className="App">
      {!noSidebarPaths.includes(location.pathname) && <Sidebar />}
      <div className="inner">
        <Routes>
          <Route path="/" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/change-password" element={<ChangePassword />} />

          <Route
            path="/home"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/create-teacher"
            element={
              <ProtectedRoute>
                <CreateTeacher />
              </ProtectedRoute>
            }
          />

          <Route
            path="/classes/create"
            element={
              <ProtectedRoute>
                <CreateClass />
              </ProtectedRoute>
            }
          />

          <Route
            path="/profile/:id"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />

          <Route
            path="/classes/:id/home"
            element={
              <ProtectedRoute>
                <ClassHome />
              </ProtectedRoute>
            }
          />

          <Route
            path="/classes/:id/members"
            element={
              <ProtectedRoute>
                <ClassMembers />
              </ProtectedRoute>
            }
          />

          <Route
            path='/assignments/:id/team-submissions'
            element={<ProtectedRoute><TeamSubmissionsRoute /></ProtectedRoute>}
          />

          <Route
            path="/assignments/:id"
            element={
              <ProtectedRoute>
                <Assignment />
              </ProtectedRoute>
            }
          />

          <Route
            path="/assignments/:id/group"
            element={
              <ProtectedRoute>
                <Group />
              </ProtectedRoute>
            }
          />

          <Route
            path="/student/review-history"
            element={
              <ProtectedRoute>
                <ReviewHistoryPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/assignments/:id/reviews"
            element={
              <ProtectedRoute>
                <TeacherReviewsPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/admin/users"
            element={
              <ProtectedRoute>
                <AdminUsersPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/assignments/:id/analytics"
            element={
              <ProtectedRoute>
                <AssignmentAnalytics />
              </ProtectedRoute>
            }
          />

          <Route
            path="/activity"
            element={
              <ProtectedRoute>
                <ActivityFeedPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/teacher/assignments/:assignmentId/rubric"
            element={
              <ProtectedRoute>
                <RubricBuilderPage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/student/feedback/:id"
            element={
              <ProtectedRoute>
                <FeedbackView />
              </ProtectedRoute>
            }
          />

          <Route
            path='/classes/:courseId/progress'
            element={
              <ProtectedRoute><StudentProgressPage /></ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;