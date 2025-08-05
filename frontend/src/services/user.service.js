// src/services/user.service.js
import apiClient from './http.service';

class UserService {
    /**
     * Get current user data
     * @returns {Promise} - Promise resolving to user data
     */
    getCurrentUser() {
        return apiClient.get('users/me/');
    }

    // Email verification methods - disabled as email verification is no longer required
    // /**
    //  * Verify user email with token
    //  * @param {string} token - Email verification token
    //  * @returns {Promise} - Promise resolving to response data
    //  */
    // verifyEmail(token) {
    //     return apiClient.post('users/verify-email/', { token });
    // }

    // /**
    //  * Request a new verification email
    //  * @param {string} email - Optional email parameter
    //  * @returns {Promise} - Promise resolving to response data
    //  */
    // resendVerificationEmail(email) {
    //     if (email) {
    //         return apiClient.post('users/resend-verification/', { email });
    //     }
    //     return apiClient.post('users/resend-verification/');
    // }

    /**
     * Generate a new 2FA secret and QR code
     * @returns {Promise} - Promise resolving to 2FA setup data
     */
    generateTwoFactorSecret() {
        return apiClient.post('users/2fa/generate/');
    }

    /**
     * Verify and enable 2FA with a verification code
     * @param {string} code - 6-digit authentication code
     * @returns {Promise} - Promise resolving to response data
     */
    verifyTwoFactor(code) {
        return apiClient.post('users/2fa/verify/', { code });
    }

    /**
     * Disable 2FA for the current user
     * @returns {Promise} - Promise resolving to response data
     */
    disableTwoFactor() {
        return apiClient.post('users/2fa/disable/');
    }

    /**
     * Change user password
     * @param {string} currentPassword - Current password
     * @param {string} newPassword - New password
     * @returns {Promise} - Promise resolving to response data
     */
    changePassword(currentPassword, newPassword) {
        return apiClient.post('users/change-password/', {
            current_password: currentPassword,
            new_password: newPassword
        });
    }

    /**
     * Get user notification settings
     * @returns {Promise} - Promise resolving to notification settings
     */
    getNotificationSettings() {
        return apiClient.get('users/notification-settings/');
    }

    /**
     * Update user notification settings
     * @param {Object} settings - Notification settings object
     * @returns {Promise} - Promise resolving to response data
     */
    updateNotificationSettings(settings) {
        return apiClient.put('users/notification-settings/', settings);
    }

    /**
     * Export all user data
     * @returns {Promise} - Promise resolving to user data export
     */
    exportUserData() {
        return apiClient.get('users/export-data/');
    }

    /**
     * Reset user password (forgot password flow)
     * @param {string} email - User email
     * @returns {Promise} - Promise resolving to response data
     */
    resetPassword(email) {
        return apiClient.post('users/reset-password/', { email });
    }

    /**
     * Verify reset password token and set new password
     * @param {string} token - Password reset token
     * @param {string} newPassword - New password
     * @returns {Promise} - Promise resolving to response data
     */
    confirmResetPassword(token, newPassword) {
        return apiClient.post('users/reset-password/confirm/', {
            token,
            new_password: newPassword
        });
    }
}

export default new UserService();