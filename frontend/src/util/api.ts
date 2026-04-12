import { didExpire, removeToken } from "./login";

const BASE_URL = 'http://localhost:5000'

export const maybeHandleExpire = (response: Response) => {
  if (didExpire(response)) {
    removeToken();
    window.location.href = '/';
  }
}

export const tryLogin = async (email: string, password: string) => {
  const response = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email: email, password: password }),
    credentials: 'include'
  });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.msg || 'Invalid email or password');
  }

  const json = await response.json();
  localStorage.setItem('user', JSON.stringify(json));
  return json;
}

export const tryRegister = async (name: string, email: string, password: string) => {
  try {
    const response = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
      headers: {
        'Content-Type': 'application/json'
      },
    });
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(error);
  }
}

export const createClass = async (name: string) => {
  const response = await fetch(`${BASE_URL}/class/create_class`, {
    method: 'POST',
    body: JSON.stringify({ name }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);
  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return response
}

export const listClasses = async () => {
  const resp = await fetch(`${BASE_URL}/class/classes`, {
    method: 'GET',
    credentials: 'include'
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

export const importStudentsForCourse = async (courseID: number, students: string) => {
  const response = await fetch(`${BASE_URL}/class/enroll_students`, {
    method: 'POST',
    body: JSON.stringify({ students, class_id: courseID }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);
  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
}

export const listAssignments = async (classId: string) => {
  const resp = await fetch(`${BASE_URL}/assignment/` + classId, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

export const listStuGroup = async (assignmentId: number, studentId: number) => {
  const resp = await fetch(`${BASE_URL}/list_stu_groups/` + assignmentId + "/" + studentId, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

// NOTE: listGroups was removed — it was an exact duplicate of listAllGroups.
// Use listAllGroups(assignmentId) for all group fetching needs.

export const listUnassignedGroups = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/list_ua_groups/` + assignmentId, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

export const listCourseMembers = async (classId: string) => {
  const resp = await fetch(`${BASE_URL}/class/classes/members`, {
    method: 'POST',
    body: JSON.stringify({ id: classId }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

export const listGroupMembers = async (assignmentId: number, groupID: number) => {
  const resp = await fetch(`${BASE_URL}/list_group_members/` + assignmentId + '/' + groupID, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

export const getUserId = async () => {
  const resp = await fetch(`${BASE_URL}/user_id`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

export const saveGroups = async (groupID: number, userID: number, assignmentID: number) => {
  const resp = await fetch(`${BASE_URL}/save_groups`, {
    method: 'POST',
    body: JSON.stringify({ groupID, userID, assignmentID }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
}

export const getCriteria = async (rubricID: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/criteria?rubricID=${rubricID}`, {
    credentials: 'include'
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json()
}

export const createCriteria = async (rubricID: number, question: string, scoreMax: number, canComment: boolean, hasScore: boolean = true) => {
  const response = await fetch(`${BASE_URL}/assignment/rubric/${rubricID}/criteria`, {
    method: 'POST',
    body: JSON.stringify({ question, scoreMax, hasScore, canComment }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);
  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
}

export const createRubric = async (assignmentID: number, canComment: boolean): Promise<{ id: number }> => {
  const response = await fetch(`${BASE_URL}/assignment/${assignmentID}/rubric`, {
    method: 'POST',
    body: JSON.stringify({ canComment }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);
  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return await response.json();
}

export const getRubric = async (rubricID: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/rubric/by-id?rubricID=${rubricID}`, {
    credentials: 'include'
  });
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return await resp.json();
}

export const createAssignment = async (courseID: number, name: string, description_html = '') => {
  const response = await fetch(`${BASE_URL}/assignment/create_assignment`, {
    method: 'POST',
    body: JSON.stringify({ courseID, name, description_html }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);
  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return await response.json();
}

export const deleteGroup = async (groupID: number) => {
  const resp = await fetch(`${BASE_URL}/delete_group`, {
    method: 'POST',
    body: JSON.stringify({ groupID }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  })
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
}

// NOTE: createReview and createCriterion were removed — use submitReview() instead.
// submitReview() calls POST /api/reviews/submit and handles both in one atomic request.

export const getReview = async (assignmentID: number, reviewerID: number, revieweeID: number) => {
  const resp = await fetch(
    `${BASE_URL}/assignment/review?assignmentID=${assignmentID}&reviewerID=${reviewerID}&revieweeID=${revieweeID}`,
    { credentials: 'include' }
  )
  maybeHandleExpire(resp);
  if (!resp.ok) {
    throw new Error(`Response status: ${resp.status}`);
  }
  return resp
}

export const getNextGroupID = async (assignmentID: number) => {
  const response = await fetch(`${BASE_URL}/next_groupid?assignmentID=${assignmentID}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);
  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return await response.json();
}

export const createGroup = async (assignmentID: number, name: string, id: number) => {
  const response = await fetch(`${BASE_URL}/create_group`, {
    method: "POST",
    body: JSON.stringify({ assignmentID, name, id }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  })
  maybeHandleExpire(response);
  if (!response.ok) {
    throw new Error(`Response status: ${response.status}`);
  }
  return await response.json();
}

export const createTeacherAccount = async (name: string, email: string, password: string) => {
  const response = await fetch(`${BASE_URL}/admin/users/create`, {
    method: 'POST',
    body: JSON.stringify({ name, email, password, role: 'teacher', must_change_password: true }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });
  maybeHandleExpire(response);
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.msg || `Response status: ${response.status}`);
  }
  return await response.json();
}

export const changePassword = async (currentPassword: string, newPassword: string) => {
  const response = await fetch(`${BASE_URL}/user/password`, {
    method: 'PUT',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include'
  });
  maybeHandleExpire(response);
  if (!response.ok) {
    const errorData = await response.json();
    if (errorData.failures && errorData.failures.length > 0) {
      throw new Error(errorData.failures.join('\n'));
    }
    throw new Error(errorData.error || errorData.msg || `Response status: ${response.status}`);
  }
  return await response.json();
}

// ── Review history ────────────────────────────────────────────────────────────

export const getMyReviews = async (): Promise<Response> => {
  const response = await fetch(`${BASE_URL}/review-history/my-reviews`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(response);
  return response;
};

export const getMyTrends = async (): Promise<Response> => {
  const response = await fetch(`${BASE_URL}/review-history/my-trends`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(response);
  return response;
};

// ── Review file attachments ───────────────────────────────────────────────────

export const uploadReviewFiles = async (reviewID: number, files: File[]) => {
  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${BASE_URL}/review/${reviewID}/upload`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    });
    maybeHandleExpire(response);
    if (!response.ok) throw new Error(`Response status: ${response.status}`);
  }
};

export const getReviewFiles = async (reviewId: number) => {
  const resp = await fetch(`${BASE_URL}/review/${reviewId}/files`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const downloadReviewFile = (fileId: number): string =>
  `${BASE_URL}/review/file/${fileId}`;

// ── Teacher reviews ───────────────────────────────────────────────────────────

export interface TeacherReviewRow {
  review_id: number;
  reviewer_id: number;
  reviewee_id: number;
  total_score: number;
  has_conclusion: boolean;
}

export interface TeacherReviewCriterion {
  criterion_id: number | null;
  criterion_name: string;
  score: number | null;
  score_max: number | null;
  comment: string;
}

export interface TeacherConclusion {
  id?: number;
  review_id?: number;
  teacher_id?: number;
  note: string;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface TeacherReviewDetail {
  review_id: number;
  reviewer_id: number;
  reviewee_id: number;
  criteria: TeacherReviewCriterion[];
  conclusion: TeacherConclusion | null;
}

export const teacherListReviews = async (
  assignmentId: number,
  groupId = "",
  sort = "id"
): Promise<TeacherReviewRow[]> => {
  const resp = await fetch(
    `${BASE_URL}/teacher/assignments/${assignmentId}/reviews?group_id=${groupId}&sort=${sort}`,
    { method: "GET", credentials: "include" }
  );
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const teacherGetReviewDetail = async (
  assignmentId: number,
  reviewId: number
): Promise<TeacherReviewDetail> => {
  const resp = await fetch(
    `${BASE_URL}/teacher/assignments/${assignmentId}/reviews/${reviewId}`,
    { method: "GET", credentials: "include" }
  );
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const teacherSaveConclusion = async (
  reviewId: number,
  note: string
): Promise<TeacherConclusion> => {
  const resp = await fetch(`${BASE_URL}/teacher/reviews/${reviewId}/conclusion`, {
    method: "POST",
    body: JSON.stringify({ note }),
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });
  maybeHandleExpire(resp);
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.error || `Response status: ${resp.status}`);
  }
  return await resp.json();
};

export const listAllGroups = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/list_all_groups/${assignmentId}`, {
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

// ── Assignment file attachment ────────────────────────────────────────────────

export const uploadAssignmentFile = async (assignmentId: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await fetch(`${BASE_URL}/assignment/${assignmentId}/upload`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.msg || `Response status: ${resp.status}`);
  }
  return await resp.json();
};

export const downloadAssignmentAttachment = async (assignmentId: number, filename: string) => {
  const resp = await fetch(`${BASE_URL}/assignment/${assignmentId}/attachment`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

export const deleteAssignmentAttachment = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/${assignmentId}/attachment`, {
    method: 'DELETE',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

// ── Assignment detail ─────────────────────────────────────────────────────────

export const getAssignment = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/detail/${assignmentId}`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

// ── Rubric by assignment ──────────────────────────────────────────────────────

export const getRubricByAssignment = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/${assignmentId}/rubric`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

// ── Submit review ─────────────────────────────────────────────────────────────

export const submitReview = async (payload: ReviewSubmission) => {
  const resp = await fetch(`${BASE_URL}/api/reviews/submit`, {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) {
    const data = await resp.json().catch(() => ({}));
    throw new Error(data.msg || `Response status: ${resp.status}`);
  }
  return await resp.json();
};

// ── Student grades & feedback ─────────────────────────────────────────────────

export const getStudentGrades = async () => {
  const resp = await fetch(`${BASE_URL}/student/grades`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const getStudentFeedback = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/student/assignments/${assignmentId}/feedback`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

// ── Conclusion file attachments ───────────────────────────────────────────────

export const uploadConclusionFile = async (assignmentId: number, file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const resp = await fetch(`${BASE_URL}/assignment/${assignmentId}/conclusion/upload`, {
    method: 'POST',
    body: formData,
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const listConclusionFiles = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/${assignmentId}/conclusion/files`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const downloadConclusionFile = async (assignmentId: number, fileId: number) => {
  const resp = await fetch(
    `${BASE_URL}/assignment/${assignmentId}/conclusion/file/${fileId}`,
    { method: 'GET', credentials: 'include' }
  );
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `conclusion_file_${fileId}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};

// ── User profile ──────────────────────────────────────────────────────────────

export const getUserProfile = () =>
  fetch(`${BASE_URL}/user/profile`, { credentials: 'include' }).then(res => {
    maybeHandleExpire(res);
    return res;
  });

export const updateUserProfile = (data: { name?: string; first_name?: string; last_name?: string }) =>
  fetch(`${BASE_URL}/user/profile`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(res => {
    maybeHandleExpire(res);
    return res;
  });

// ── Admin user management ─────────────────────────────────────────────────────

export interface AdminUserPayload {
  name: string;
  email: string;
  password?: string;
  role: string;
}

export const adminListUsers = (page = 1, role = '', search = '') =>
  fetch(`${BASE_URL}/admin/users?page=${page}&role=${role}&search=${encodeURIComponent(search)}`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const adminCreateUser = (data: AdminUserPayload) =>
  fetch(`${BASE_URL}/admin/users/create`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(res => { maybeHandleExpire(res); return res; });

export const adminUpdateUser = (id: number, data: Partial<AdminUserPayload>) =>
  fetch(`${BASE_URL}/admin/users/${id}`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(res => { maybeHandleExpire(res); return res; });

export const adminDeactivateUser = (id: number) =>
  fetch(`${BASE_URL}/admin/users/${id}/deactivate`, {
    method: 'PATCH',
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const adminReactivateUser = (id: number) =>
  fetch(`${BASE_URL}/admin/users/${id}/reactivate`, {
    method: 'PATCH',
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

// ── Teacher analytics ─────────────────────────────────────────────────────────

export interface CriterionStat {
  criterion_id: number;
  criterion_name: string;
  score_max: number;
  avg_score: number;
  response_count: number;
}

export interface AnalyticsData {
  assignment_id: number;
  assignment_name: string;
  completion_pct: number;
  total_students: number;
  submitted: number;
  criteria: CriterionStat[];
  outliers: {
    review_id: number;
    reviewer_id: number;
    reviewee_id: number;
    total_score: number;
    deviation: number;
  }[];
}

export const getAssignmentAnalytics = (assignmentId: number) =>
  fetch(`${BASE_URL}/teacher/assignments/${assignmentId}/analytics`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const exportReviewsCSV = (assignmentId: number) =>
  fetch(`${BASE_URL}/teacher/assignments/${assignmentId}/export`, {
    credentials: 'include',
  });

// ── Announcements ─────────────────────────────────────────────────────────────

export const getCourseAnnouncements = (courseId: number) =>
  fetch(`${BASE_URL}/announcement/course/${courseId}/announcements`, {
    credentials: 'include',
  }).then((res) => { maybeHandleExpire(res); return res; });

export const createAnnouncement = (courseId: number, data: { title: string; content: string }) =>
  fetch(`${BASE_URL}/announcement/course/${courseId}/announcements`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then((res) => { maybeHandleExpire(res); return res; });

export const deleteAnnouncement = (id: number) =>
  fetch(`${BASE_URL}/announcement/announcements/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  }).then((res) => { maybeHandleExpire(res); return res; });

// ── Notifications ─────────────────────────────────────────────────────────────

export const getNotifications = (page = 1, perPage = 20, type?: string) => {
  const params = new URLSearchParams({ page: String(page), per_page: String(perPage) });
  if (type) params.append('type', type);
  return fetch(`${BASE_URL}/notification/notifications?${params}`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });
};

export const getUnreadCount = () =>
  fetch(`${BASE_URL}/notification/notifications/unread-count`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const markNotificationRead = (id: number) =>
  fetch(`${BASE_URL}/notification/notifications/${id}/read`, {
    method: 'PUT',
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const markAllNotificationsRead = () =>
  fetch(`${BASE_URL}/notification/notifications/read-all`, {
    method: 'PUT',
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

// ── Rubric Builder ────────────────────────────────────────────────────────────

export const getRubricBuilder = (assignmentId: number) =>
  fetch(`${BASE_URL}/rubric-builder/assignment/${assignmentId}/rubric`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const upsertRubric = (assignmentId: number, data: Record<string, unknown>) =>
  fetch(`${BASE_URL}/rubric-builder/assignment/${assignmentId}/rubric`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }).then(res => { maybeHandleExpire(res); return res; });

export const reorderCriteria = (rubricId: number, order: number[]) =>
  fetch(`${BASE_URL}/rubric-builder/rubric/${rubricId}/reorder`, {
    method: 'PUT',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order }),
  }).then(res => { maybeHandleExpire(res); return res; });

export const getRubricTemplates = () =>
  fetch(`${BASE_URL}/rubric-builder/templates`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const applyRubricTemplate = (templateId: number, assignmentId: number) =>
  fetch(`${BASE_URL}/rubric-builder/templates/${templateId}/apply/${assignmentId}`, {
    method: 'POST',
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

// ── PDF Report Export ─────────────────────────────────────────────────────────

export const exportAssignmentPDF = async (assignmentId: number): Promise<Blob> => {
  const res = await fetch(`${BASE_URL}/teacher/assignments/${assignmentId}/export-pdf`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(res);
  if (!res.ok) throw new Error('Failed to export PDF');
  return res.blob();
};

// ── In-Group Messaging ────────────────────────────────────────────────────────

export interface ChatMessage {
  id: number;
  sender_id: number;
  sender_name: string;
  content: string;
  created_at: string;
  is_read: boolean;
  group_id?: number;
  recipient_id?: number;
}

export const getGroupMessages = (groupId: number) =>
  fetch(`${BASE_URL}/message/group/${groupId}`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const sendGroupMessage = (groupId: number, content: string) =>
  fetch(`${BASE_URL}/message/group/${groupId}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  }).then(res => { maybeHandleExpire(res); return res; });

export const markGroupMessagesRead = (groupId: number) =>
  fetch(`${BASE_URL}/message/group/${groupId}/read`, {
    method: 'PUT',
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const getDirectMessages = (otherUserId: number) =>
  fetch(`${BASE_URL}/message/direct/${otherUserId}`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

export const sendDirectMessage = (otherUserId: number, content: string) =>
  fetch(`${BASE_URL}/message/direct/${otherUserId}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  }).then(res => { maybeHandleExpire(res); return res; });

export const markDirectMessagesRead = (otherUserId: number) =>
  fetch(`${BASE_URL}/message/direct/${otherUserId}/read`, {
    method: 'PUT',
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

// ── Student Progress Dashboard (US5) ─────────────────────────────────────────

export const getCourseProgress = (courseId: number) =>
  fetch(`${BASE_URL}/teacher/classes/${courseId}/progress`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

// ── Team Submissions (US22) ───────────────────────────────────────────────────

export const getTeamSubmissions = (assignmentId: number) =>
  fetch(`${BASE_URL}/student/assignments/${assignmentId}/team-submissions`, {
    credentials: 'include',
  }).then(res => { maybeHandleExpire(res); return res; });

// ── Assignment management (US9) ───────────────────────────────────────────────

export const editAssignment = async (
  assignmentId: number,
  payload: { name?: string; description_html?: string }
) => {
  const resp = await fetch(`${BASE_URL}/assignment/edit_assignment/${assignmentId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  });
  maybeHandleExpire(resp);
  if (resp.status === 403) throw new Error('Cannot edit an assignment past its due date.');
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const deleteAssignment = async (assignmentId: number) => {
  const resp = await fetch(`${BASE_URL}/assignment/delete_assignment/${assignmentId}`, {
    method: 'DELETE',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (resp.status === 403) throw new Error('Cannot delete an assignment past its due date.');
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  return await resp.json();
};

export const downloadTeamReviewFile = async (fileId: number) => {
  const resp = await fetch(`${BASE_URL}/student/review-file/${fileId}/download`, {
    method: 'GET',
    credentials: 'include',
  });
  maybeHandleExpire(resp);
  if (!resp.ok) throw new Error(`Response status: ${resp.status}`);
  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `review_file_${fileId}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
};