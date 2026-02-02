<?php
/**
 * Email Functions (using Resend API)
 */

require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/functions.php';

/**
 * Send email via Resend API
 */
function sendEmail($to, $subject, $html) {
    $settings = getSiteSettings();
    $apiKey = $settings['resend_api_key'] ?: RESEND_API_KEY;
    $sender = $settings['resend_sender_email'] ?: SENDER_EMAIL;
    
    if (empty($apiKey) || empty($sender) || empty($to)) {
        return false;
    }
    
    $data = [
        'from' => $sender,
        'to' => [$to],
        'subject' => $subject,
        'html' => $html
    ];
    
    $options = [
        'http' => [
            'header' => [
                "Content-Type: application/json",
                "Authorization: Bearer $apiKey"
            ],
            'method' => 'POST',
            'content' => json_encode($data)
        ]
    ];
    
    $context = stream_context_create($options);
    $result = @file_get_contents('https://api.resend.com/emails', false, $context);
    
    return $result !== false;
}

/**
 * Send submission received email
 */
function sendSubmissionEmail($email, $submission) {
    if (empty($email)) return;
    
    $submitUrl = SITE_URL . '/submit.php';
    
    $html = '
    <html>
    <body style="font-family: \'Courier New\', monospace; background-color: #0a0a0a; color: #00FF41; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; border: 2px solid #00FF41; padding: 20px;">
            <h1 style="color: #00FF41; border-bottom: 1px solid #00FF41; padding-bottom: 10px;">
                DOWNLOAD ZONE - SUBMISSION RECEIVED
            </h1>
            <p>Your submission has been received and is pending admin approval.</p>
            
            <h2 style="color: #00FFFF;">SUBMISSION DETAILS:</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Name:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">' . htmlspecialchars($submission['name'] ?? 'N/A') . '</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Type:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">' . htmlspecialchars($submission['type'] ?? 'N/A') . '</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Category:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">' . htmlspecialchars($submission['category'] ?? 'N/A') . '</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">File Size:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">' . htmlspecialchars($submission['file_size'] ?? 'N/A') . '</td>
                </tr>
            </table>
            
            <p style="margin-top: 20px;">
                <a href="' . $submitUrl . '" style="display: inline-block; padding: 10px 20px; background-color: #00FF41; color: #000; text-decoration: none; font-weight: bold;">
                    SUBMIT ANOTHER FILE
                </a>
            </p>
            
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                This is an automated message from Download Zone.
            </p>
        </div>
    </body>
    </html>';
    
    sendEmail($email, "Download Zone - Submission Received: " . ($submission['name'] ?? 'Unknown'), $html);
}

/**
 * Send approval notification email
 */
function sendApprovalEmail($email, $submission) {
    if (empty($email)) return;
    
    $homeUrl = SITE_URL;
    
    $html = '
    <html>
    <body style="font-family: \'Courier New\', monospace; background-color: #0a0a0a; color: #00FF41; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; border: 2px solid #00FF41; padding: 20px;">
            <h1 style="color: #00FF41; border-bottom: 1px solid #00FF41; padding-bottom: 10px;">
                DOWNLOAD ZONE - SUBMISSION APPROVED
            </h1>
            <p style="color: #00FF41; font-size: 16px;">Great news! Your submission has been approved and is now live on Download Zone.</p>
            
            <h2 style="color: #00FFFF;">APPROVED CONTENT:</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Name:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">' . htmlspecialchars($submission['name'] ?? 'N/A') . '</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Type:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">' . htmlspecialchars($submission['type'] ?? 'N/A') . '</td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #333; color: #888;">Category:</td>
                    <td style="padding: 8px; border: 1px solid #333; color: #00FF41;">' . htmlspecialchars($submission['category'] ?? 'N/A') . '</td>
                </tr>
            </table>
            
            <p style="margin-top: 20px;">
                <a href="' . $homeUrl . '" style="display: inline-block; padding: 10px 20px; background-color: #00FF41; color: #000; text-decoration: none; font-weight: bold;">
                    VIEW ON DOWNLOAD ZONE
                </a>
            </p>
            
            <p style="margin-top: 30px; font-size: 12px; color: #666;">
                Thank you for contributing to Download Zone!
            </p>
        </div>
    </body>
    </html>';
    
    sendEmail($email, "Download Zone - Submission Approved: " . ($submission['name'] ?? 'Unknown'), $html);
}

/**
 * Send admin notification for new submissions
 */
function sendAdminSubmissionNotification($submissions) {
    $settings = getSiteSettings();
    $adminEmail = $settings['admin_email'] ?? '';
    
    if (empty($adminEmail)) return;
    
    $count = count($submissions);
    $items = '';
    foreach (array_slice($submissions, 0, 50) as $s) {
        $items .= '<li><b>' . htmlspecialchars($s['name'] ?? 'N/A') . '</b> (' . htmlspecialchars($s['type'] ?? 'N/A') . ')</li>';
    }
    
    $html = "
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>New submissions received</h2>
      <p>Count: $count</p>
      <ul>$items</ul>
    </body></html>";
    
    sendEmail($adminEmail, "New submissions received ($count)", $html);
}

/**
 * Send password reset email
 */
function sendPasswordResetEmail($email, $resetLink, $type = 'user') {
    $title = $type === 'admin' ? 'Reset Admin Password' : 'Reset your password';
    
    $html = "
    <html><body style='font-family: Arial, sans-serif;'>
      <h2>$title</h2>
      <p>Click the link below to reset your password. This link expires in 30 minutes.</p>
      <p><a href='$resetLink'>Reset password</a></p>
    </body></html>";
    
    sendEmail($email, $title, $html);
}
