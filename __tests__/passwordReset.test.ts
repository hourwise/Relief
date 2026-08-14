import { isPasswordRecoveryUrl } from '../src/utils/passwordRecovery';
import { describeAuthError, isPlausibleEmail } from '../src/utils/authErrors';
import { assertEqual, assertTrue, section } from './helpers/harness';

section('password recovery contract');
assertTrue('recovery query is recognised', isPasswordRecoveryUrl('relief://auth/callback?type=recovery'));
assertTrue('recovery token is recognised', isPasswordRecoveryUrl('relief://auth/callback#access_token=token'));
assertEqual('ordinary app link is not recovery', isPasswordRecoveryUrl('relief://home'), false);
assertEqual('reset fallback is safe', describeAuthError({ message: 'unknown server detail' }, 'password_reset'), 'Could not start password recovery. Please try again.');
assertEqual('expired recovery is safe', describeAuthError({ code: 'otp_expired' }, 'password_update'), 'That recovery link has expired. Request a new password-reset email.');
assertTrue('reset form uses same email validation', isPlausibleEmail('person@example.com'));
