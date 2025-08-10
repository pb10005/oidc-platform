// OIDC Authentication Server - Client-side JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                form.classList.add('was-validated');
                return false;
            }
            // Form is valid, allow submission
            form.classList.add('was-validated');
        }, false);
    });

    // Password confirmation validation
    const passwordField = document.getElementById('password');
    const confirmPasswordField = document.getElementById('confirm_password');
    
    if (passwordField && confirmPasswordField) {
        function validatePasswordMatch() {
            if (passwordField.value !== confirmPasswordField.value) {
                confirmPasswordField.setCustomValidity('Passwords do not match');
            } else {
                confirmPasswordField.setCustomValidity('');
            }
        }
        
        passwordField.addEventListener('input', validatePasswordMatch);
        confirmPasswordField.addEventListener('input', validatePasswordMatch);
    }

    // Auto-hide alerts after configurable seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            const hideSeconds = window.appConfig?.alertAutoHideSeconds || 5;
            setTimeout(function() {
                alert.style.transition = 'opacity 0.5s';
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.remove();
                }, 500);
            }, hideSeconds * 1000);
        }
    });

    // Loading state for forms
    const submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const form = button.closest('form');
            if (form && form.checkValidity()) {
                // Don't prevent default - let the form submit normally
                button.disabled = true;
                button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
                
                // Re-enable button after configurable seconds as fallback
                const timeoutSeconds = window.appConfig?.formLoadingTimeoutSeconds || 10;
                setTimeout(function() {
                    button.disabled = false;
                    button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
                }, timeoutSeconds * 1000);

                // Submit the form
                form.submit();
            } else {
                // If form is invalid, prevent submission and show validation
                event.preventDefault();
                form.classList.add('was-validated');
            }
        });
        
        // Store original button text
        button.setAttribute('data-original-text', button.innerHTML);
    });

    // PKCE (Proof Key for Code Exchange) implementation
    window.PKCEUtils = {
        // Generate a cryptographically random string
        generateRandomString: function(length) {
            const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
            let result = '';
            const randomValues = new Uint8Array(length);
            crypto.getRandomValues(randomValues);
            
            for (let i = 0; i < length; i++) {
                result += charset[randomValues[i] % charset.length];
            }
            return result;
        },

        // Generate code verifier
        generateCodeVerifier: function() {
            return this.generateRandomString(128);
        },

        // Generate code challenge from verifier
        generateCodeChallenge: async function(verifier) {
            const encoder = new TextEncoder();
            const data = encoder.encode(verifier);
            const digest = await crypto.subtle.digest('SHA-256', data);
            
            // Convert to base64url
            return btoa(String.fromCharCode(...new Uint8Array(digest)))
                .replace(/\+/g, '-')
                .replace(/\//g, '_')
                .replace(/=/g, '');
        },

        // Store PKCE values in sessionStorage
        storePKCEValues: function(verifier, challenge) {
            sessionStorage.setItem('pkce_verifier', verifier);
            sessionStorage.setItem('pkce_challenge', challenge);
        },

        // Retrieve PKCE verifier
        getCodeVerifier: function() {
            return sessionStorage.getItem('pkce_verifier');
        },

        // Clear PKCE values
        clearPKCEValues: function() {
            sessionStorage.removeItem('pkce_verifier');
            sessionStorage.removeItem('pkce_challenge');
        }
    };

    // OAuth2 client helper functions
    window.OAuth2Client = {
        // Build authorization URL with PKCE
        buildAuthorizationUrl: async function(config) {
            const verifier = window.PKCEUtils.generateCodeVerifier();
            const challenge = await window.PKCEUtils.generateCodeChallenge(verifier);
            
            window.PKCEUtils.storePKCEValues(verifier, challenge);
            
            const params = new URLSearchParams({
                response_type: 'code',
                client_id: config.clientId,
                redirect_uri: config.redirectUri,
                scope: config.scope || 'openid profile email',
                state: config.state || window.PKCEUtils.generateRandomString(32),
                code_challenge: challenge,
                code_challenge_method: 'S256'
            });
            
            if (config.nonce) {
                params.append('nonce', config.nonce);
            }
            
            return `${config.authorizationEndpoint}?${params.toString()}`;
        },

        // Exchange authorization code for tokens
        exchangeCodeForTokens: async function(config) {
            const verifier = window.PKCEUtils.getCodeVerifier();
            if (!verifier) {
                throw new Error('No PKCE verifier found');
            }
            
            const params = new URLSearchParams({
                grant_type: 'authorization_code',
                code: config.code,
                redirect_uri: config.redirectUri,
                client_id: config.clientId,
                code_verifier: verifier
            });
            
            if (config.clientSecret) {
                params.append('client_secret', config.clientSecret);
            }
            
            const response = await fetch(config.tokenEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: params.toString()
            });
            
            if (!response.ok) {
                throw new Error(`Token exchange failed: ${response.statusText}`);
            }
            
            const tokens = await response.json();
            window.PKCEUtils.clearPKCEValues();
            
            return tokens;
        }
    };

    // Utility functions
    window.Utils = {
        // Parse URL parameters
        getUrlParams: function() {
            const params = new URLSearchParams(window.location.search);
            const result = {};
            for (const [key, value] of params) {
                result[key] = value;
            }
            return result;
        },

        // Show toast notification
        showToast: function(message, type = 'info') {
            const toast = document.createElement('div');
            toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
            toast.style.top = '20px';
            toast.style.right = '20px';
            toast.style.zIndex = '9999';
            toast.innerHTML = `
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            `;
            
            document.body.appendChild(toast);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                toast.remove();
            }, 5000);
        }
    };
});
