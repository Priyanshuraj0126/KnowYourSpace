import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
import {
    getAuth,
    GoogleAuthProvider,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    signInWithPopup,
    updateProfile
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";

const form = document.getElementById('firebase-auth-form');
const message = document.getElementById('auth-message');
const googleButton = document.getElementById('google-auth-button');
const config = window.KYS_FIREBASE_CONFIG || {};

function showMessage(text, type = 'error') {
    message.hidden = false;
    message.textContent = text;
    message.dataset.type = type;
}

function formatAuthError(error) {
    const code = error?.code || '';
    if (code === 'auth/unauthorized-domain') {
        return `Google sign-in is not enabled for ${window.location.hostname}. Add this host in Firebase Authentication > Settings > Authorized domains, or open the app on localhost.`;
    }
    return (error?.message || 'Authentication failed.').replace('Firebase: ', '');
}

function firebaseReady() {
    return config.apiKey && config.authDomain && config.projectId && config.appId;
}

async function createServerSession(user) {
    const idToken = await user.getIdToken();
    const response = await fetch('/api/auth/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ idToken })
    });
    const data = await response.json();
    if (!response.ok || !data.success) {
        throw new Error(data.error || 'Could not create server session.');
    }
    window.location.href = data.redirect || '/profile';
}

if (!firebaseReady()) {
    showMessage('Firebase web config is missing. Add FIREBASE_API_KEY, FIREBASE_AUTH_DOMAIN, FIREBASE_PROJECT_ID, and FIREBASE_APP_ID to .env.');
    form?.addEventListener('submit', (event) => event.preventDefault());
    form?.querySelectorAll('button').forEach((button) => {
        button.disabled = true;
    });
} else if (form) {
    const app = initializeApp(config);
    const auth = getAuth(app);
    const googleProvider = new GoogleAuthProvider();
    googleProvider.setCustomParameters({ prompt: 'select_account' });

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        const submitButton = form.querySelector('button[type="submit"]');
        const mode = form.dataset.mode;
        const email = document.getElementById('auth-email').value.trim();
        const password = document.getElementById('auth-password').value;
        const nameInput = document.getElementById('auth-name');

        submitButton.disabled = true;
        showMessage('Connecting to Firebase...', 'info');

        try {
            let credential;
            if (mode === 'signup') {
                credential = await createUserWithEmailAndPassword(auth, email, password);
                if (nameInput && nameInput.value.trim()) {
                    await updateProfile(credential.user, { displayName: nameInput.value.trim() });
                }
            } else {
                credential = await signInWithEmailAndPassword(auth, email, password);
            }
            await createServerSession(credential.user);
        } catch (error) {
            showMessage(formatAuthError(error));
        } finally {
            submitButton.disabled = false;
        }
    });

    if (googleButton) {
        googleButton.addEventListener('click', async () => {
            googleButton.disabled = true;
            showMessage('Opening Google sign-in...', 'info');

            try {
                const credential = await signInWithPopup(auth, googleProvider);
                await createServerSession(credential.user);
            } catch (error) {
                showMessage(formatAuthError(error));
            } finally {
                googleButton.disabled = false;
            }
        });
    }
}
