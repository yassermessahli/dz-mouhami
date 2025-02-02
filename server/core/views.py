# views.py

from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.permissions import IsAuthenticated
from .models import Address, LawyerProfile, LawyerImage, LawyerDocument , ClientProfile , User , TimeSlot , Review , Appointment , ClientImage
from .serializers import AddressSerializer, LawyerProfileSerializer, LawyerImageSerializer, LawyerDocumentSerializer , ClientProfileSerializer , TimeSlotSerializer \
    , ReviewSerializer , AppointmentSerializer , ClientImageSerializer
from django.contrib.auth.models import Group
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from allauth.socialaccount.models import SocialAccount, SocialToken
from rest_framework import generics, permissions
from .models import LawyerProfile, Appointment
from .serializers import UserSerializer
from django.contrib.auth.models import User
from .serializers import LawyerProfileAdminListSerializer
from django.utils import timezone
from django.db.models import Q

from allauth.socialaccount.models import SocialAccount
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound
from django.db.models import Avg
from .serializers import LawyerProfileAdminListSerializer
from rest_framework import generics
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import Http404,request

# samy's import 
from django.urls import reverse
from django.conf import settings
from django.shortcuts import redirect



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info_from_google_token(request):
    google_token = request.data.get('google_token', None)

    if not google_token:
        return Response({'error': 'Google token not provided'}, status=400)

    try:
        social_account = SocialAccount.objects.get(token=google_token, provider='google')

        user_profile = social_account.user.userprofile  

        user_info = {
            'username': user_profile.user.username,
            'email': user_profile.user.email,
            'first_name': user_profile.user.first_name,
            'last_name': user_profile.user.last_name,
        }

        return Response(user_info, status=200)

    except SocialAccount.DoesNotExist:
        return Response({'error': 'Invalid Google token'}, status=400)




# class GoogleAccessTokenView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         try:
#             google_account = SocialAccount.objects.get(user=request.user, provider='google')
#             google_token = google_account.socialtoken_set.get()
#             access_token = str(google_token.token)  # Convert the SocialToken to a string
#             return Response({'access_token': access_token})
#         except SocialAccount.DoesNotExist:
#             return Response({'error': 'No linked Google account for the user.'}, status=404)
#         except SocialToken.DoesNotExist:
#             return Response({'error': 'No Google access token found for the user.'}, status=404)
#         except Exception as e:
#             return Response({'error': f'An error occurred: {str(e)}'}, status=500)



class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer

class TimeSlotViewSet(viewsets.ModelViewSet):
    queryset = TimeSlot.objects.all()
    serializer_class = TimeSlotSerializer



class LawyerImageViewSet(viewsets.ModelViewSet):
    serializer_class = LawyerImageSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lawyer_profile_pk = self.kwargs['lawyer_pk']
        context['lawyer_profile_pk'] = lawyer_profile_pk
        return context
    
    def get_queryset(self):
        lawyer_profile_pk = self.kwargs['lawyer_pk']
        return LawyerImage.objects.filter(lawyer_id=lawyer_profile_pk)
    

class ClientImageViewSet(viewsets.ModelViewSet):
    serializer_class = ClientImageSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # user = self.request.data['token']
        token = 'ec3cce742b1fc84f23c0b427dffeb9890cd3041e'
        user = Token.objects.get(key=token).user
        context['user'] = user
        return context
    
    def get_queryset(self):
        user = self.request.user
        return ClientImage.objects.filter(user=user)



class LawyerDocumentViewSet(viewsets.ModelViewSet):
    queryset = LawyerDocument.objects.all()
    serializer_class = LawyerDocumentSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        lawyer_profile_pk = self.kwargs['lawyer_pk']
        context['lawyer_profile_pk'] = lawyer_profile_pk
        return context    

    def get_queryset(self):
        ##
        lawyer_profile_pk = self.kwargs['lawyer_pk']
        return LawyerDocument.objects.filter(lawyer_id=lawyer_profile_pk)  


class LawyerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = LawyerProfileSerializer
    
    
    
    def get_queryset(self):
        token = self.request.headers.get('Authorization')
        if token:
            try:
                user = Token.objects.get(key=token).user
                if LawyerProfile.objects.get(user=user):
                    return LawyerProfile.objects.get(user=user)
            except Token.DoesNotExist:
                raise PermissionDenied('Not authenticated')
        else :
            raise PermissionDenied("No token provided")
            
        # # token = "6aaeffb7d25c4697859f4135245956eec6012708"
        # # token = '6aaeffb7d25c4697859f4135245956eec6012708'
        # # token = "533ba7c8dccd71003fedea92076ab3ef94aaa243"
        # user = Token.objects.get(key=token).user
        # return LawyerProfile.objects.get(user=user)


    def perform_create(self, serializer):
        token = self.request.headers.get('Authorization')
        if token:
            try:
                user = Token.objects.get(key=token).user
            except Token.DoesNotExist:
                raise PermissionDenied('Lawyer profile not found or not approved.')
        else :
            return PermissionDenied("access denied")
            
        # token = "6aaeffb7d25c4697859f4135245956eec6012708"
        # token = "533ba7c8dccd71003fedea92076ab3ef94aaa243"
        user = Token.objects.get(key=token).user

        # token = '6aaeffb7d25c4697859f4135245956eec6012708'
        # user = Token.objects.get(key=token).user
        # Check if the user is a client
        if ClientProfile.objects.filter(user=user).exists():
            raise PermissionDenied('Clients cannot create a lawyer profile')

        # Check if a lawyer profile already exists for the user
        if LawyerProfile.objects.filter(user=user).exists():
            raise PermissionDenied('Lawyer profile already exists for the user')

        # Save the lawyer profile
        serializer.save(user=user)

        # Add the user to the 'Lawyer' group
        if user.is_authenticated and not user.groups.filter(name='Lawyer').exists():
            group_name = 'Lawyer'
            group, created = Group.objects.get_or_create(name=group_name)
            user.groups.add(group)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Check if the lawyer profile is approved
        if not instance.approved:
            raise NotFound('Lawyer profile not found or not approved.')

        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset)

        # Calculate and include the rating information in the serialized response
        data = serializer.data
        lawyer_id = data['id']
        rating = Review.objects.filter(lawyer__id=lawyer_id).aggregate(Avg('rating'))['rating__avg']
        data['rating'] = rating

        return Response(data, status=status.HTTP_200_OK)
    
    # def perform_update(self, serializer):
    #     token = self.request.headers.get('Authorization')
    #     if token:
    #         try:
    #             user = Token.objects.get(key=token).user
    #         except Token.DoesNotExist:
    #             raise PermissionDenied('Lawyer profile not found or not approved.')
    #     else :
    #         return PermissionDenied("access denied")
            
    #     # token = "6aaeffb7d25c4697859f4135245956eec6012708"
    #     # token = "533ba7c8dccd71003fedea92076ab3ef94aaa243"
    #     user = Token.objects.get(key=token).user
    #     # Check if the user is a client
    #     if ClientProfile.objects.filter(user=user).exists():
    #         raise PermissionDenied('You are a Client!')

    #     # Save the lawyer profile
    #     serializer.save(user=user)
            


class ClientProfileViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = ClientProfile.objects.all()
    serializer_class = ClientProfileSerializer



    def get_queryset(self):
        token = self.request.headers.get('Authorization')
        if token:
            try:
                user = Token.objects.get(key=token).user
            except Token.DoesNotExist:
                raise PermissionDenied('Client profile not found')
        
        else :
            return PermissionDenied("access denied")
            
        
        # token = 'fa5b5b71139ace340120b57070f14a5429764199'
        user = Token.objects.get(key=token).user
        if LawyerProfile.objects.filter(user=user).exists():
            raise PermissionDenied('Lawyers cannot see a client profile')
        else:
            return ClientProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        token = self.request.headers.get('Authorization')
        if token:
            try:
                user = Token.objects.get(key=token).user
            except Token.DoesNotExist:
                raise PermissionDenied('Lawyer profile not found or not approved.')
        else :
            return PermissionDenied("access denied")


        # token = 'ec3cce742b1fc84f23c0b427dffeb9890cd3041e'
        # token = 'fa5b5b71139ace340120b57070f14a5429764199'
        user = Token.objects.get(key=token).user
        if LawyerProfile.objects.filter(user=user).exists():
            raise PermissionDenied('Lawyers cannot create a client profile')

        if ClientProfile.objects.filter(user=user).exists():
            raise PermissionDenied('Client profile already exists for the user')
        else:
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
                

from .pagination import DefaultPagination

class LawyerAdminDashboardViewSet(viewsets.ModelViewSet):
    # sort by Approved=false comes before those with Approved=true
    queryset = LawyerProfile.objects.prefetch_related('image', 'documents').order_by('approved').all()
    pagination_class = DefaultPagination
    # permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    serializer_class = LawyerProfileAdminListSerializer

    def create(self, request, *args, **kwargs):
        return Response({'error': 'Method Not Allowed'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def perform_update(self, serializer):
        token = self.request.headers.get('Authorization')
        if token:
            try:
                user = Token.objects.get(key=token).user
            except Token.DoesNotExist:
                raise PermissionDenied('access denied.')
        else :
            return PermissionDenied("access denied")
        
        # token = '6aaeffb7d25c4697859f4135245956eec6012708'
        user = Token.objects.get(key=token).user
        if user.is_superuser:

            instance = serializer.save()

        # Check if 'approved' was updated to True
        if serializer.validated_data.get('approved', False) and not instance.approved:
            # Send email to the lawyer
            subject = 'Your Lawyer Profile has been approved'
            message = 'Your lawyer profile has been approved. You can now use our platform.'
            from_email = 'settings.EMAIL_HOST_USER'  # Make sure to replace this with your actual sender email
            to_email = [instance.user.email]  # Assuming the lawyer's email is stored in the User model

            send_mail(subject, message, from_email, to_email, fail_silently=False)





class LawyerViewSet(viewsets.ModelViewSet):
    queryset = LawyerProfile.objects.prefetch_related('image').all()
    serializer_class = LawyerProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['user__first_name', 'user__last_name', 'address__city' , 'specialization' , 'address__state' , 'address__country']
    http_method_names = ['get']

    def get_queryset(self):
        queryset = super().get_queryset()
        name = self.request.query_params.get('name', None)
        city = self.request.query_params.get('city', None)
        specialization = self.request.query_params.get('specialization', None)
        state = self.request.query_params.get('state', None)
        country = self.request.query_params.get('country', None)

        if name:
            queryset = queryset.filter(user__first_name__icontains=name) | queryset.filter(user__last_name__icontains=name)

        if city:
            queryset = queryset.filter(address__city__icontains=city)

        if specialization:
            queryset = queryset.filter(specialization__icontains=specialization)

        if state:
            queryset = queryset.filter(address__state__icontains=state)

        if country:
            queryset = queryset.filter(address__country__icontains=country)

        return queryset
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # Calculate and include the rating information in the serialized response
        data = serializer.data
        for item in data:
            lawyer_id = item['id']
            rating = Review.objects.filter(lawyer__id=lawyer_id).aggregate(Avg('rating'))['rating__avg']
            item['rating'] = rating

        return Response(data)




# class LawyerSearchCatViewSet(viewsets.ModelViewSet):
#     queryset = LawyerProfile.objects.all()
#     serializer_class = LawyerProfileSerializer
#     filter_backends = [DjangoFilterBackend, filters.SearchFilter]
#     search_fields = ['user__first_name', 'user__last_name', 'address__city', 'specialization']
#     method = ['GET']

#     def get_queryset(self):
#         queryset = super().get_queryset()
#         name = self.request.query_params.get('name', None)
#         city = self.request.query_params.get('city', None)
#         specialization = self.request.query_params.get('specialization', None)

#         if name:
#             queryset = queryset.filter(user__first_name__icontains=name) | queryset.filter(user__last_name__icontains=name)

#         if city:
#             queryset = queryset.filter(address__city__icontains=city)

#         if specialization:
#             queryset = queryset.filter(specialization__icontains=specialization)

#         return queryset

# class AppointmentLawyerModelViewSet(viewsets.ModelViewSet):
#     serializer_class = AppointmentSerializer

#     def get_queryset(self):
#         # Assuming the user is a lawyer
#         lawyer = self.request.user.lawyer_profile
#         return Appointment.objects.filter(lawyer=lawyer)    





# class AppointmentClientModelViewSet(viewsets.ModelViewSet):
#     serializer_class = AppointmentSerializer

#     def get_queryset(self):
#         lawyer_id = self.kwargs.get('lawyer_pk')
#         if lawyer_id:
#             lawyer = get_object_or_404(LawyerProfile, id=lawyer_id)
#             return Appointment.objects.filter(lawyer=lawyer, client=self.request.user.client_profile)
#         else:
#             return Appointment.objects.none()


#     def get_serializer_context(self):
#         context = super().get_serializer_context()
#         lawyer_id = self.kwargs.get('lawyer_pk')
#         context['lawyer_profile'] = LawyerProfile.objects.get(id=lawyer_id)
#         context['client_profile'] = ClientProfile.objects.get(user=self.request.user)
#         return context   
    # def perform_create(self, serializer):
    #     lawyer_id = self.kwargs.get('lawyer_pk')
    #     print(lawyer_id + "pasdfhosapfdhpsahfd;ksahfkashfk;af;khasfkashfkahfahflshafdlkhalfdkhsakfhakfdsh")
    #     if lawyer_id:
    #         lawyer_profile = get_object_or_404(LawyerProfile, id=lawyer_id)

    #         if hasattr(self.request.user, 'client_profile'):
    #             client_profile = self.request.user.client_profile


 
                

    #             if serializer.is_valid():
    #                 serializer.save()
    #                 return Response(serializer.data, status=status.HTTP_201_CREATED)
    #             else:
    #                 return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    #         else:
    #             return Response({"error": "Only clients can create appointments."}, status=status.HTTP_403_FORBIDDEN)
    #     else:
    #         return Response({"error": "Invalid lawyer ID."}, status=status.HTTP_400_BAD_REQUEST)



class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        lawyer_id = self.kwargs.get('lawyer_pk')
        return Review.objects.filter(lawyer__id=lawyer_id)

    def perform_create(self, serializer):
        lawyer_id = self.kwargs.get('lawyer_pk')
        lawyer = get_object_or_404(LawyerProfile, id=lawyer_id)
        serializer.validated_data['lawyer'] = lawyer
        serializer.save()

        #to calculate the average rating
        new_rating = serializer.validated_data['rating']
        existing_reviews = Review.objects.filter(lawyer=lawyer)
        average_rating = existing_reviews.aggregate(Avg('rating'))['rating__avg']
        lawyer.rating = average_rating
        lawyer.save()

    def get_serializer_context(self):
        token = self.request.headers.get('Authorization')
        if token:
            try:
                user = Token.objects.get(key=token).user
            except Token.DoesNotExist:
                raise PermissionDenied('Lawyer profile not found or not approved.')
        else :
            return PermissionDenied("access denied")


        # token = 'ec3cce742b1fc84f23c0b427dffeb9890cd3041e'
        user = Token.objects.get(key=token).user
        client = ClientProfile.objects.get(user=user)
        return {'lawyer_id': self.kwargs['lawyer_pk'] , 'client_id': client.id}


# def index(request,):
#     if request.method == 'POST':
#         message = request.POST['message']
#         email = request.POST['email']
#         name = request.POST['name']
#         send_mail(
#             name,  # title
#             message,  # message
#             'settings.EMAIL_HOST_USER',  # sender
#             [email],
#             fail_silently=False
#         )
#     return response()  # put the response

#--------------------------------------------samy 3amkom --------------------------------------------

from django.contrib.auth.models import User

from django.http import JsonResponse
from django.urls import reverse

from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.db import models
from .utils import google_callback
from .models import UserProfile
from django.shortcuts import redirect
from django.urls import reverse
from .utils import google_setup
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import redirect
import json

class GoogleOAuth2SignUpView(APIView):
    def get(self, request):
        redirect_uri = request.build_absolute_uri(reverse("google_signup_callback"))
        return redirect(google_setup(redirect_uri))
    
class GoogleOAuth2SignUpCallbackView(APIView):
    def get(self, request):
        redirect_uri = request.build_absolute_uri(reverse("google_signup_callback"))
        auth_uri = request.build_absolute_uri()

        user_data = google_callback(redirect_uri, auth_uri)

        # Use get_or_create since an existing user may end up signing in
        # through the sign up route.
        user, _ = User.objects.get_or_create(
            email=user_data["email"],
            username=user_data["given_name"],
            defaults={"first_name": user_data["given_name"],"last_name": user_data["family_name"]},
        )

        # Populate the extended user data stored in UserProfile.
        UserProfile.objects.get_or_create(
            user=user, defaults={"google_id": user_data["id"]}
        )
        try:
            ClientImage.objects.get_or_create(user=user , defaults={"image": user_data["picture"]})
        except:
            pass

        # Create the auth token for the frontend to use.
        token, _ = Token.objects.get_or_create(user=user)

        # Here we assume that once we are logged in we should send
        # a token to the frontend that a framework like React or Angular
        # can use to authenticate further requests.
        frontend_url = "http://localhost:3000/login-handler"
        is_superuser = user.is_superuser
        is_lawyer = hasattr(user,'lawyer_profile')
        is_client = hasattr(user,'client_profile')
        return redirect(frontend_url + "?token=" + token.key+"&data="+json.dumps(user_data) + "&signup=true" + "&is_superuser="+str(is_superuser)+"&is_lawyer="+str(is_lawyer)+"&is_client="+str(is_client))
        return JsonResponse({"data":user_data,"token": token.key})

class GoogleOAuth2LoginView(APIView):
    def get(self, request):
        # The redirect_uri should match the settings shown on the GCP OAuth config page.
        # The call to build_absolute_uri returns the full URL including domain.
        redirect_uri = request.build_absolute_uri(reverse("google_login_callback"))
        return redirect(google_setup(redirect_uri))

class GoogleOAuth2LoginCallbackView(APIView):
    def get(self, request):
        redirect_uri = request.build_absolute_uri(reverse("google_login_callback"))
        auth_uri = request.build_absolute_uri()

        user_data = google_callback(redirect_uri, auth_uri)

        try:
            user = User.objects.get(username=user_data["email"])
        except User.DoesNotExist:
            return redirect("http://localhost:8000/core/signup")

        # Create the auth token for the frontend to use.
        token, _ = Token.objects.get_or_create(user=user)

        # Here we assume that once we are logged in we should send
        # a token to the frontend that a framework like React or Angular
        # can use to authenticate further requests.
        frontend_url = "http://localhost:3000/login-handler"
        is_superuser = user.is_superuser
        is_lawyer = hasattr(user,'lawyer_profile')
        is_client = hasattr(user,'client_profile')
        return redirect(frontend_url + "?token=" + token.key+"&data="+json.dumps(user_data)+"&is_superuser="+str(is_superuser)+"&is_lawyer="+str(is_lawyer)+"&is_client="+str(is_client))
        return JsonResponse({"token": token.key,"data": user_data})


class CustomPageNumberPagination(PageNumberPagination):
    page_size_query_param = 'limit'
    max_page_size = 100

@api_view(['GET'])
def lawyer_profile_search(request):
    query = request.GET.get('query', '')
    categories = request.GET.getlist('categories')
    days = request.GET.getlist('days')

    rating = request.GET.get('rating', '')

    search_results = LawyerProfile.objects.filter(approved=True)

    if query :
        lawyer_filter = (
            Q(user__first_name__icontains = query) |
            Q(user__last_name__icontains = query)
        )
        address_filter = (
            Q(address__street__icontains = query) |
            Q(address__city__icontains = query) |
            Q(address__state__icontains = query) |
            Q(address__country__icontains = query)
        )

        search_results = search_results.filter(lawyer_filter | address_filter)
    
    if days != ['']:
        day_filter = Q()
        for day in days:
            day_filter |= Q(time_slots__day__iexact=day)
        search_results = search_results.filter(day_filter)
    
    if categories != [''] :
        category_filter = Q()
        for category in categories:
            category_filter |= Q(specialization__iexact=category)
        search_results = search_results.filter(category_filter)

    if rating:
        search_results = search_results.filter(rating__gte=rating)
        
    search_results = search_results.order_by('-rating')
    
    paginator = CustomPageNumberPagination()
    paginated_results = paginator.paginate_queryset(search_results, request)

    serialized_results = LawyerProfileSerializer(paginated_results, many=True).data

    lawyer_ids = [result['id'] for result in serialized_results]  
    lawyer_images = LawyerImage.objects.filter(lawyer_id__in=lawyer_ids)
    serialized_images = LawyerImageSerializer(lawyer_images, many=True).data

    image_dict = {image['id']: image['image'] for image in serialized_images}

    for result in serialized_results:
        result['image'] = image_dict.get(result['id'], None)
    
    return Response({'search_results': serialized_results, 'num_pages': paginator.page.paginator.num_pages})


from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['POST']) #client
@authentication_classes([])
@permission_classes([AllowAny])
def schedule_appointment(request, lawyer_id, time_slot_id):
    token_key = request.headers.get('Authorization', None)
    time = request.POST.get('startTime',"9:00:00")
    note = request.POST.get('note','')
    
    if token_key:
        try:
            user = Token.objects.get(key=token_key).user
        except Token.DoesNotExist:
            return Response({"success": False, "message": "Access denied. Invalid token."})
    else:
        return Response({"success": False, "message": "Access denied. Token not provided."})
    

    if hasattr(user,'client_profile'):
        try:
            time_slot = get_object_or_404(TimeSlot, id=time_slot_id, lawyer_id=lawyer_id)
        except Http404:
            return Response({"success": False, "message": "Time slot doesn't exist."})
        
        check_existing_appointment = Appointment.objects.filter(
            time_slot_id = time_slot_id,
            client_id = user.client_profile
        ).first()
        if check_existing_appointment:
            return Response({"success": False, "message": "Appointment already exists."})
        
        lawyer_profile = LawyerProfile.objects.get(id=lawyer_id)
        appointment = Appointment.objects.create(
            time_slot = time_slot,
            lawyer = lawyer_profile,
            client = user.client_profile,
            start_time = time,
            note = note,
            status = "Pending"
        )
        appointment.save()
        return Response({"success": True, "message": "Appointment scheduled successfully."})
    else:
        return Response({"success": False, "message": "You don't have permission to schedule an appointment."})
    

@api_view(['GET']) #lawyer
@authentication_classes([])  # No authentication classes for unauthenticated access
@permission_classes([AllowAny])  # Allow access to anyone, authenticated or not
def appointments_requests(request):
    token_key = request.headers.get('Authorization', None)

    if token_key:
        try:
            user = Token.objects.get(key=token_key).user
        except Token.DoesNotExist:
            return Response({"success": False, "message": "Access denied. Invalid token."})
    else:
        return Response({"success": False, "message": "Access denied. Token not provided."})

    if hasattr(user, 'lawyer_profile'):
        try:
            appointments = Appointment.objects.filter(lawyer_id=user.lawyer_profile, status='Pending')
            appointments = appointments.order_by('-date',)
                        
            serialized_results = AppointmentSerializer(appointments, many=True).data

            return Response({"success": True, "results": serialized_results}) #add the success variable
        
        except Http404:
            return Response({"success": False, "message": "No appointments for this user"})
    else:
        return Response({"success": False, "message": "User has no lawyer profile."})


@api_view(['GET']) #lawyer
@authentication_classes([])
@permission_classes([AllowAny])  
def appointments(request):
    token_key = request.headers.get('Authorization', None)

    if token_key:
        try:
            user = Token.objects.get(key=token_key).user
        except Token.DoesNotExist:
            return Response({"success": False, "message": "Access denied. Invalid token."})
    else:
        return Response({"success": False, "message": "Access denied. Token not provided."})

    if hasattr(user, 'lawyer_profile'):
        try:
            appointments = Appointment.objects.filter(lawyer_id=user.lawyer_profile, status='Accepted')
            appointments = appointments.order_by('-date',)
                        
            serialized_results = AppointmentSerializer(appointments, many=True).data

            return Response({"success": True, "results": serialized_results}) #add the success variable
        except Http404:
            return Response({"success": False, "message": "No appointments for this user"})
    else:
        return Response({"success": False, "message": "User has no lawyer profile."})


@api_view(['POST']) #lawyer
@authentication_classes([])
@permission_classes([AllowAny])  
def accept_appointment(request, appointment_id):
    token_key = request.headers.get('Authorization', None)
    
    if token_key:
        try:
            user = Token.objects.get(key=token_key).user
        except Token.DoesNotExist:
            return Response('Access denied. Invalid token.', status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response("Access denied. Token not provided.", status=status.HTTP_401_UNAUTHORIZED)

    if hasattr(user, 'lawyer_profile'):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, lawyer=user.lawyer_profile)
        except Http404:
            return Response({"success": False, "message": "Appointment not found or not associated with your profile"})
        appointment.status = 'Accepted'
        appointment.save()
        return Response({"success": True, "message": "Appointment accepted."}, status=status.HTTP_201_CREATED)
    else:
        return Response({"success": False, "message": "You don't have permission to accept an appointment."})

@api_view(['POST']) #lawyer
def refuse_appointment(request, appointment_id):
    token_key = request.headers.get('Authorization', None)
    
    if token_key:
        try:
            user = Token.objects.get(key=token_key).user
        except Token.DoesNotExist:
            raise PermissionDenied('Access denied. Invalid token.')
    else:
        return PermissionDenied("Access denied. Token not provided.")

    if hasattr(user, 'lawyer_profile'):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, lawyer=user.lawyer_profile)
        except Http404:
            return Response({"success": False, "message": "Appointment not found or not associated with your profile."})
        
        appointment.status = 'Refused'
        appointment.save()
        return Response({"success": True, "message": "Appointment refused."})
    else:
        return Response({"success": False, "message": "You don't have permission to refused an appointment."})


def verify_token(request):
    token = request.headers.get('Authorization', None)
    if token:
        try:
            user = Token.objects.get(key=token).user
        except Token.DoesNotExist:
            return Response({"success": False, "message": "Invalid token."})
        else:
            return Response({"success": True, "message": "Valid token."})
    else:
        return Response({"success": False, "message": "Token not provided."})
    

# Lawyer dashboard views

# list all appointments of the lawyer
class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    def list(self, request, *args, **kwargs):
        user_token = request.headers.get('Authorization', None)
        try:
            token = Token.objects.get(key=user_token)
            try:
                queryset = Appointment.objects.filter(lawyer=token.user.lawyer_profile)
                serializer = AppointmentSerializer(queryset, many=True)
                return Response(serializer.data)
            except LawyerProfile.DoesNotExist:
                return Response({"success": False, "message": "Is not a lawyer"})
        except Token.DoesNotExist:
            return Response({"success": False, "message": "not authenticated"})



# return some statistics about the appointments of the lawyer
@api_view(['GET'])
def appointments_statistics_view(request):
    user_token = request.headers.get('Authorization', None)
    try:
        user = Token.objects.get(key=user_token).user
        if hasattr(user, "lawyer_profile"):
            lawyer = user.lawyer_profile
            all_appointments = lawyer.appointments.all().count()
            
            today = timezone.now()
            start_of_week = today - timezone.timedelta(days=6)
            appointments_of_this_week = lawyer.appointments.filter(date__range=[start_of_week, today]).count()
            
            pending_appointments = lawyer.appointments.filter(status="Pending").count()
            accepted_appointments = lawyer.appointments.filter(status="Accepted").count()
            refused_appointments = lawyer.appointments.filter(status="Refused").count()
            
            return Response({
                "success": True,
                "all_appointments": all_appointments,
                "appointments_of_this_week": appointments_of_this_week,
                "pending_appointments": pending_appointments,
                "approved_appointments": accepted_appointments,
                "refused_appointments": refused_appointments
            })
        else:
            return Response({"success": False, "message": "Is not a lawyer"})
        
    except Token.DoesNotExist:
        return Response({"success": False, "message": "Is not authenticated"})