from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import UserSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from .models import MyUser
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.http import HttpResponseRedirect

@api_view(['GET'])
def index(request):
    return Response({"Success": "The setup was successful"})

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        user.set_password(request.data['password'])  # Hash the password
        user.save()  # Now save to the DB
        token, _ = Token.objects.get_or_create(user=user)  # Generate token
        return Response({"token": token.key, "user": serializer.data}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    # Check if email and password are provided
    if not email or not password:
        return Response(
            {"detail": "Email and password are required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get user and check password
    user = get_object_or_404(MyUser, email=email)
    if not user.check_password(password):
        return Response(
            {"detail": "Invalid email or password."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate token if login is successful
    token, _ = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(instance=user)

    # Return success response with login message
    return Response(
        {
            "detail": "Login successful.",
            "token": token.key,
            "user": serializer.data
        },
        status=status.HTTP_200_OK
    )

@api_view(['POST'])
def logout(request):
    if request.user.is_authenticated:
        request.user.auth_token.delete()
        return Response(
            {
                "detail": "Logout successful."
                }, 
            status=status.HTTP_200_OK
            )
    return Response(
        {
            "detail": "User not authenticated."
        }, 
            status=status.HTTP_401_UNAUTHORIZED
                )


# Initialize the token generator to create secure tokens for password reset
token_generator = PasswordResetTokenGenerator()

@api_view(['POST'])
def request_password_reset(request):
    """
    Accepts an email address from the user and sends a password reset email
    if the email is registered in the system.
    """
    email = request.data.get('email')  # Get the email from the request data
    user = MyUser.objects.filter(email=email).first()  # Check if a user with this email exists

    if user:
        # Encode the user's ID as a URL-safe base64 string
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Generate a password reset token for the user
        token = token_generator.make_token(user)
        
        # Construct the password reset URL with UID and token as parameters
        reset_url = request.build_absolute_uri(
            reverse('password-reset-confirm', kwargs={'uid': uid, 'token': token})
        )
        
        # Send the password reset email with the generated reset URL
        send_mail(
            subject="Password Reset Request",  # Subject line of the email
            message=f"Click the link to reset your password: {reset_url}",  # Email message body with reset URL
            from_email="noreply@yourdomain.com",  # Sender's email address
            recipient_list=[user.email]  # Recipient's email address
        )

    # Response indicating email was sent, or will be if email exists
    return Response({"detail": "If an account with that email exists, a password reset link has been sent."})

# Password Reset Confirmation View

@api_view(['POST'])
def reset_password(request, uid, token):
    try:
        uid = force_str(urlsafe_base64_decode(uid))
        user = MyUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, MyUser.DoesNotExist):
        user = None

    if user and token_generator.check_token(user, token):
        password = request.data.get('password')
        password_confirmation = request.data.get('password_confirmation')
        
        # Check if both password fields match
        if password != password_confirmation:
            return Response({"detail": "Passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set the new password if they match
        user.set_password(password)
        user.save()
        
        # Redirect to the login page
        login_url = reverse('login')  # Adjust 'login' to match the URL name for your login page
        return HttpResponseRedirect(login_url)
    
    return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
