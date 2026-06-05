import sys

with open('frontend/src/App.tsx', 'r') as f:
    content = f.read()

import_line = 'import { useAuthStore } from "./store/authStore"\n'
if import_line not in content:
    content = content.replace('import React from "react"\n', 'import React from "react"\n' + import_line)

redirect_comp = '''
function RoleRedirect() {
  const { isAuthenticated, user } = useAuthStore()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  
  const role = user?.role?.name?.toLowerCase()
  if (role === 'admin') return <Navigate to="/admin/dashboard" replace />
  if (role === 'apoteker') return <Navigate to="/apoteker" replace />
  if (role === 'kasir') return <Navigate to="/pos" replace />
  return <Navigate to="/orders" replace />
}
'''

if 'function RoleRedirect' not in content:
    content = content.replace('class ErrorBoundary', redirect_comp + '\nclass ErrorBoundary')

if '<Route path="/dashboard" element={<RoleRedirect />} />' not in content:
    content = content.replace('<Routes>\n', '<Routes>\n          <Route path="/dashboard" element={<RoleRedirect />} />\n')

with open('frontend/src/App.tsx', 'w') as f:
    f.write(content)
print("Updated App.tsx successfully")
