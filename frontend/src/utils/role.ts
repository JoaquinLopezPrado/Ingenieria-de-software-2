export function normalizeRole(user: any): string {
    const rawRole =
        user?.role?.name ??
        user?.role_name ??
        user?.role ??
        ''

    return String(rawRole).trim().toLowerCase()
}

export function isAdminUser(user: any): boolean {
    const roleName = normalizeRole(user)

    return roleName === 'admin' || roleName === 'administrador'
}

export function isEmployeeUser(user: any): boolean {
    return normalizeRole(user) === 'empleado'
}