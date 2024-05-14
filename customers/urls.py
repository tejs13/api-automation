from django.urls import path

from customers.views import GenerateCustomerOTPView, VerifyOTPView, HomeScreenView, \
    GetCategoriesView, GetSubCategoriesView, GetSubSubCategoriesView, GetProductListView, \
        GetProductDetailsView, WishlistView, CartView

urlpatterns = [
    path('generate-otp', GenerateCustomerOTPView.as_view()),
    path('verify-otp', VerifyOTPView.as_view()),
    path('home-screen', HomeScreenView.as_view()),
    path('get-categories', GetCategoriesView.as_view()),
    path('get-sub-categories', GetSubCategoriesView.as_view()),
    path('get-sub-sub-categories', GetSubSubCategoriesView.as_view()),
    path('get-product-list', GetProductListView.as_view()),
    path('get-product-details/<str:product_uid>', GetProductDetailsView.as_view()),
    path('add-to-wishlist/<str:customer_uuid>/<str:product_uid>', WishlistView.as_view()),
    path('get-wishlist/<str:customer_uuid>', WishlistView.as_view()),
    path('delete-from-wishlist/<str:wishlist_id>', WishlistView.as_view()),
    path('add-to-cart', CartView.as_view()),
    path('get-cart/<str:customer_uuid>', CartView.as_view()),
    path('update-cart', CartView.as_view()),
    path('delete-from-cart/<str:cart_id>', CartView.as_view()),
    # path('register-seller', RegisterSeller.as_view()),
    # path('add-update-seller-brand/<str:seller_uuid>', SellerBrandView.as_view()),
    # path('login-seller', LoginSeller.as_view()),
    # path('add-seller-product/<str:seller_uuid>', AddSellerProductView.as_view()),
    # path('get-seller-profile/<str:seller_uuid>', GetSellerInfo.as_view()),
    # path('get-seller-product-detail/<str:product_uuid>', GetSellerProductsView.as_view()),


]

    # path('Generate-NFA/<int:rfq_no>', GetRFQDetailsView.as_view()),
    # path('get-qcs/<str:proposal_id>', GetQCSDetailsView.as_view()),
    # path('GetRFQVendorData/<int:pk>', ProposalView.as_view()),
    # path('Submit-NFA', NFAView.as_view()),
    # path('get-qcslist/', QCSListView.as_view()),]