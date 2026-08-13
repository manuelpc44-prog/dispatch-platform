class AuthUser {
  final String id;
  final String email;
  final String fullName;
  final bool isActive;
  final List<String> roles;

  AuthUser({
    required this.id,
    required this.email,
    required this.fullName,
    required this.isActive,
    required this.roles,
  });

  factory AuthUser.fromJson(Map<String, dynamic> json) {
    return AuthUser(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String,
      isActive: json['is_active'] as bool,
      roles: (json['roles'] as List).map((r) => r as String).toList(),
    );
  }

  bool get isChofer => roles.contains('CHOFER');
}
