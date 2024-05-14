from django.contrib.auth.models import User, Group
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from Sellers.models.ProductAttribute import SellerProductAttribute


from Sellers.models.ProductImages import SellerProductImages
from Sellers.models.ProductVariation import SellerProductVariation
from Sellers.models.SellerBrand import SellerBrand
from customers.models.Cart import CustomerCart
from customers.models.HomeScreen import CustomerHomescreen
from customers.models.DraftCustomer import DraftCustomer
from customers.models.Customers import Customers
from Masters.models.ProductCategory import ProductCategory
from Masters.models.ProductSubCategory import ProductSubCategory
from Masters.models.ProductSubSubCategory import ProductSubSubCategory
from Sellers.models.SellerProduct import SellerProduct
from Sellers.models.ProductDetails import SellerProductDetails
from customers.models.Wishlist import CustomerWishlist
from customers.utils import get_base_64_file


class CustomerRegisterSerializer(ModelSerializer):

    def create(self, validated_data):
        phone_number = validated_data.pop('phone_number')
        country_code = validated_data.pop('country_code')
        request = validated_data.pop('request')
        model = self.Meta.model

        cust_obj = model.objects.create(created_by=request.user.username, last_updated_by=request.user.username,
                                          phone_number=phone_number, country_code_id=country_code)

        if cust_obj:
            user_obj = User.objects.create(is_active=True, is_staff=False,
                                           username=cust_obj.phone_number)

            # mapping the Django User with creatd seller
            cust_obj.cust_user_obj = user_obj
            cust_obj.save()
            # Adding to Sellers Group
            grp, created = Group.objects.get_or_create(name="customers")
            grp = Group.objects.get(name="customers")
            grp.user_set.add(user_obj)

            # deleting the Draft Seller obj after Seller Creation
            is_d_seller_exist = DraftCustomer.objects.filter(phone_number=phone_number).exists()
            if is_d_seller_exist:
                draft_seller_obj = DraftCustomer.objects.get(phone_number=phone_number)
                draft_seller_obj.delete()

        return cust_obj

    def to_internal_value(self, data):
        internal_value = dict()

        phone_number = data.get('phone_number')
        country_code = data.get('country_code')
        request = self.context['request']

        internal_value.update({ 'request': request,
                               'phone_number': phone_number,
                                'country_code' : country_code
                               })
        return internal_value

    class Meta:
        """
        Meta
        """
        model = Customers
        fields = '__all__'


class HomeScreenSerializer(ModelSerializer):

    top_sub_cats = serializers.SerializerMethodField()
    header_banner = serializers.SerializerMethodField()
    mid_banner = serializers.SerializerMethodField()
    footer_banner = serializers.SerializerMethodField()
    top_brands = serializers.SerializerMethodField()
    featured_products = serializers.SerializerMethodField()

    def get_header_banner(self, instance):
        t = {}
        if instance.header_banner:
            t['id'] = instance.header_banner.pk
            t['image_rep'] = get_base_64_file(instance.header_banner.banner_img.path)
            return t
        else:
            return {}

    def get_mid_banner(self, instance):
        t = {}
        if instance.mid_banner:
            t['id'] = instance.mid_banner.pk
            t['image_rep'] = get_base_64_file(instance.mid_banner.banner_img.path)
            return t
        else:
            return {}

    def get_footer_banner(self, instance):
        t = {}
        if instance.footer_banner:
            t['id'] = instance.footer_banner.pk
            t['image_rep'] = get_base_64_file(instance.footer_banner.banner_img.path)
            return t
        else:
            return {}

    def get_top_sub_cats(self, instance):
        final_list = []
        all_top_cats = instance.top_sub_cats.filter(is_active=True)
        print(all_top_cats, "===========")
        for i in all_top_cats:
            t = {}
            t['id'] = i.pk
            t['name'] = i.product_sub_sub_category
            t['thumb_nail'] = get_base_64_file(i.image_rep.path)
            final_list.append(t)

        return final_list


    def get_top_brands(self, instance):
        final_list = []

        all_top_brands = instance.top_brands.filter(is_active=True)

        for i in all_top_brands:
            t = {}
            t['id'] = i.pk
            t['image_rep'] = get_base_64_file(i.brand_logo.path)
            final_list.append(t)
        return final_list


    def get_featured_products(self, instance):

        final_list = []
        all_feat_prods = instance.featured_products.filter(is_active=True)
        for i in all_feat_prods:
            t = {}
            t['id'] = i.product_uid
            thum_path = SellerProductImages.objects.get(product_id__id=i.pk, is_thumbnail=True)
            t['thumb_nail'] = get_base_64_file(thum_path.file.path),
            t['prod_name'] = i.product_name,
            t['prod_price'] = i.SELLER_PRODUCT_DETAILS.price,
            # TODO remove static and addd logic
            t['star_review'] = 4
            final_list.append(t)

        return final_list


    class Meta:
        """
        Meta
        """
        model = CustomerHomescreen
        fields = ['id', 'is_active', 'top_sub_cats', 'header_banner',
                  'mid_banner', 'footer_banner', 'top_brands', 'featured_products']



class CategoriesSerializer(ModelSerializer):
    
    """
    To serialize all product categories
    """

    class Meta:
        """
        Meta
        """
        model = ProductCategory
        fields = ['id', 'product_category']


class SubCategoriesSerializer(ModelSerializer):
    
    """
    To serialize all product sub categories of a category
    """

    class Meta:
        """
        Meta
        """
        model = ProductSubCategory
        fields = ['id', 'product_sub_category']

class SubSubCategoriesSerializer(ModelSerializer):
    
    """
    To serialize all product sub sub categories of a product category and sub category
    """

    class Meta:
        """
        Meta
        """
        model = ProductSubSubCategory
        fields = ['id', 'product_sub_sub_category']


class ProductListSerializer(ModelSerializer):
    
    seller_brand_name= serializers.CharField(source='seller_brand_id.brand_name')
    discount_percent= serializers.SerializerMethodField() 
    discounted_price= serializers.SerializerMethodField()
    regular_price= serializers.SerializerMethodField()
    thumbnail_url= serializers.SerializerMethodField()
    
    def get_discount_percent(self, obj):
        id= obj.id
        product_details= SellerProductDetails.objects.get(product_id=id)
        discount_percent= product_details.discount_percent
        self.discount_percent= discount_percent
        return discount_percent

    def get_discounted_price(self, obj):
        id= obj.id
        variations= SellerProductVariation.objects.filter(product_id=id)

        prices=[]

        for variation in variations:
            price= variation.price
            prices.append(price)

        discounted_price= min(prices)
        self.discounted_price= discounted_price
        return discounted_price

    def get_regular_price(self, obj):
        discounted_price= self.discounted_price
        discount_percent= self.discount_percent
        regular_price= discounted_price/(1-(discount_percent/100))
        return round(regular_price, 2)


    def get_thumbnail_url(self, obj):
        id= obj.id
        request = self.context.get("request")
        
        product_thumbnail= SellerProductImages.objects.get(product_id=id, is_thumbnail=True)

        thumbnail = product_thumbnail.file

        return request.build_absolute_uri(thumbnail.url)



    class Meta:
        """
        Meta
        """
        model = SellerProduct
        fields = ['id', 'product_uid', 'seller_brand_name', 'product_name', 'thumbnail_url', 
        'discounted_price', 'discount_percent', 'regular_price']

    
class ProductDetailSerializer(ModelSerializer):
    seller_first_name= serializers.CharField(source='seller_id.f_name')
    seller_last_name= serializers.CharField(source='seller_id.l_name')
    seller_brand_name= serializers.CharField(source='seller_brand_id.brand_name')
    category_name= serializers.CharField(source='category_id.product_category')
    sub_category_name= serializers.CharField(source='sub_category_id.product_sub_category')
    sub_sub_category_name= serializers.CharField(source='sub_sub_category_id.product_sub_sub_category')
    seller_brand_logo= serializers.SerializerMethodField()
    product_attributes_values= serializers.SerializerMethodField()
    product_details= serializers.SerializerMethodField()
    product_images= serializers.SerializerMethodField()
    product_variations= serializers.SerializerMethodField()


    def get_seller_brand_logo(self, obj):
        logo = obj.seller_brand_id.brand_logo
        request = self.context.get("request")

        return request.build_absolute_uri(logo.url)


    def get_product_attributes_values(self, obj):
        id= obj.id
        attributes_values= SellerProductAttribute.objects.filter(product_id=id)

        res=[]

        for attribute in attributes_values:
            product_attr_id= attribute.id
            attr_name= attribute.attribute.attribute_name
            attr_value= attribute.attribute_value.attribute_value

            res.append({"product_attr_id": product_attr_id, "attr_name":attr_name, "attr_value": attr_value})

        return res
    
    def get_product_details(self,obj):
        id= obj.id

        res= {}

        product_details= SellerProductDetails.objects.get(product_id=id)

        res["is_returnable"]= product_details.is_returnable
        res["is_refundable"]= product_details.is_refundable
        res["tax_percent"]= product_details.tax_percent
        res["discount_percent"]= product_details.discount_percent
        res["product_summarry"]= product_details.product_summary
        res["addition_remarks"]= product_details.addition_remarks
        res["shipping_charges"]= product_details.shipping_charges
        res["is_free_shipping"]= product_details.is_free_shipping

        return res
    
    def get_product_images(self, obj):
        id= obj.id
        request = self.context.get("request")

        product_images=[]
        images= SellerProductImages.objects.filter(product_id= id)

        for image in images:
            img_id= image.id
            img= image.file
            is_thumbnail= image.is_thumbnail
            img_url= request.build_absolute_uri(img.url)
            

            product_images.append({"image_id":img_id, "image_url":img_url, "is_thumbnail":is_thumbnail})

        return product_images

    def get_product_variations(self, obj):
        id= obj.id
        product_variations=[]

        variations= SellerProductVariation.objects.filter(product_id= id, is_active=True)

        for variation in variations:
            size_id= variation.size_id.id
            size_name= variation.size_id.size
            price= variation.price
            stock= variation.stock

            product_variations.append({"size_id":size_id, "size_name":size_name, "price":price, "stock":stock})
        
        return product_variations

    class Meta:
        """
        Meta
        """
        model = SellerProduct
        fields = ['id', 'seller_id', 'seller_first_name', 'seller_last_name','seller_brand_id', 
        'seller_brand_name', 'seller_brand_logo', 'product_uid', 'product_sku', 'product_barcode', 
        'category_id', 'category_name', 'sub_category_id', 'sub_category_name', 'sub_sub_category_id', 
        'sub_sub_category_name', 'product_name', 'product_brief', 'product_remarks', 'product_attributes_values', 
        'product_details', 'product_images',
        'product_variations']


class WishlistSerializer(ModelSerializer):
    
    def create(self, validated_data):
        customer_id= validated_data.get('customer_id')
        product_id= validated_data.get('product_id')
        model = self.Meta.model
        request= self.context.get("request")
        

        customer_wishlist_obj= model.objects.create(customer_id= customer_id, 
        product_id= product_id, created_by=request.user.username, 
        last_updated_by=request.user.username)

        return customer_wishlist_obj

    def to_internal_value(self, data):
        internal_value = {}

        customer_uuid = data.get('customer_uuid')
        product_uid = data.get('product_uid')
        request = self.context['request']

        customer_obj= Customers.objects.get(cust_uuid=customer_uuid)
        product_obj = SellerProduct.objects.get(product_uid= product_uid)

        internal_value.update({ 'request': request,
                               'customer_id': customer_obj,
                                'product_id' : product_obj
                               })
        return internal_value

        
    class Meta:
        """
        Meta
        """
        model = CustomerWishlist
        fields = '__all__'

class AllWishlistSerializer(ModelSerializer):
    product_uid= serializers.UUIDField(source='product_id.product_uid')
    product_name= serializers.CharField(source='product_id.product_name')
    product_brand_id= serializers.IntegerField(source='product_id.seller_brand_id.id')
    product_brand_name= serializers.CharField(source='product_id.seller_brand_id.brand_name')
    product_attributes_values= serializers.SerializerMethodField()
    discount_percent= serializers.SerializerMethodField()
    discounted_price= serializers.SerializerMethodField()
    regular_price= serializers.SerializerMethodField()
    thumbnail_url= serializers.SerializerMethodField()


    def get_product_attributes_values(self, obj):
        id= obj.product_id
        attributes_values= SellerProductAttribute.objects.filter(product_id=id)

        res=[]

        for attribute in attributes_values:
            product_attr_id= attribute.id
            attr_name= attribute.attribute.attribute_name
            attr_value= attribute.attribute_value.attribute_value

            res.append({"product_attr_id": product_attr_id, "attr_name":attr_name, "attr_value": attr_value})

        return res

    def get_discount_percent(self, obj):
        id= obj.product_id
        product_details= SellerProductDetails.objects.get(product_id=id)
        discount_percent= product_details.discount_percent
        self.discount_percent= discount_percent
        return discount_percent

    def get_discounted_price(self, obj):
        id= obj.product_id
        variations= SellerProductVariation.objects.filter(product_id=id)

        prices=[]

        for variation in variations:
            price= variation.price
            prices.append(price)

        discounted_price= min(prices)
        self.discounted_price= discounted_price
        return discounted_price


    def get_regular_price(self, obj):
        discounted_price= self.discounted_price
        discount_percent= self.discount_percent
        regular_price= discounted_price/(1-(discount_percent/100))
        return round(regular_price, 2)

    def get_thumbnail_url(self, obj):
        id= obj.product_id
        request = self.context.get("request")
        
        product_thumbnail= SellerProductImages.objects.get(product_id=id, is_thumbnail=True)

        thumbnail = product_thumbnail.file

        return request.build_absolute_uri(thumbnail.url)
    

    class Meta:
        """
        Meta
        """
        model = CustomerWishlist
        fields = ['id', 'product_id', 'product_uid', 'product_name', 'product_brand_id',
        'product_brand_name', 'product_attributes_values', 'discount_percent', 'discounted_price', 
        'regular_price', 'thumbnail_url']

class CartSerializer(ModelSerializer):
    
    def create(self, validated_data):
        customer_id=validated_data.get("customer_id")
        product_variation_id= validated_data.get("product_variation_id")
        quantity= validated_data.get("quantity")
        model = self.Meta.model
        request= self.context.get("request")
        

        customer_cart_obj= model.objects.create(customer_id= customer_id, 
        product_variation_id= product_variation_id, quantity=quantity ,created_by=request.user.username, 
        last_updated_by=request.user.username)

        return customer_cart_obj

    def update(self, instance, validated_data):
        instance.customer_id= validated_data.get("customer_id")
        instance.product_variation_id= validated_data.get("product_variation_id")
        instance.quantity= validated_data.get("quantity")
        instance.last_created_by = validated_data.get('request').user.username
        instance.last_updated_by = validated_data.get('request').user.username
        instance.save()
        return instance

    def to_internal_value(self, data):
        internal_value = {}

        customer_uuid= data.get('customer_uuid')
        product_variation_id= data.get('product_variation_id')
        quantity= data.get('quantity')
        request = self.context['request']

        customer_obj= Customers.objects.get(cust_uuid= customer_uuid)
        product_variation_obj= SellerProductVariation.objects.get(id=product_variation_id)

        internal_value.update({ 'request': request,
                               'customer_id': customer_obj,
                                'product_variation_id' : product_variation_obj,
                                'quantity': quantity
                               })
        return internal_value
        
    class Meta:
        """
        Meta
        """
        model = CustomerCart
        fields = '__all__'

class AllCartSerializer(ModelSerializer):
    product_id= serializers.UUIDField(source='product_variation_id.product_id.id')
    product_uid= serializers.UUIDField(source='product_variation_id.product_id.product_uid')
    product_name= serializers.CharField(source='product_variation_id.product_id.product_name')
    product_brand_id= serializers.IntegerField(source='product_variation_id.product_id.seller_brand_id.id')
    product_brand_name= serializers.CharField(source='product_variation_id.product_id.seller_brand_id.brand_name')
    discounted_price= serializers.CharField(source='product_variation_id.price')
    size_id= serializers.CharField(source='product_variation_id.size_id.id')
    size_name= serializers.CharField(source='product_variation_id.size_id.size')
    product_attributes_values= serializers.SerializerMethodField()
    discount_percent= serializers.SerializerMethodField()
    regular_price= serializers.SerializerMethodField()
    thumbnail_url= serializers.SerializerMethodField()

 
    def get_product_attributes_values(self, obj):
        id= obj.product_variation_id.product_id
        attributes_values= SellerProductAttribute.objects.filter(product_id=id)

        res=[]

        for attribute in attributes_values:
            product_attr_id= attribute.id
            attr_name= attribute.attribute.attribute_name
            attr_value= attribute.attribute_value.attribute_value

            res.append({"product_attr_id": product_attr_id, "attr_name":attr_name, "attr_value": attr_value})

        return res

    def get_discount_percent(self, obj):
        id= obj.product_variation_id.product_id
        product_details= SellerProductDetails.objects.get(product_id=id)
        discount_percent= product_details.discount_percent
        self.discount_percent= discount_percent
        return discount_percent

    def get_regular_price(self, obj):
        discounted_price= obj.product_variation_id.price
        discount_percent= self.discount_percent
        regular_price= discounted_price/(1-(discount_percent/100))
        return round(regular_price, 2)

    def get_thumbnail_url(self, obj):
        id= obj.product_variation_id.product_id
        request = self.context.get("request")
        
        product_thumbnail= SellerProductImages.objects.get(product_id=id, is_thumbnail=True)

        thumbnail = product_thumbnail.file

        return request.build_absolute_uri(thumbnail.url)

    class Meta:
        """
        Meta
        """
        model = CustomerCart
        fields = ['id', 'quantity', 'product_id', 'product_uid', 'product_name', 'product_brand_id',
        'product_brand_name', 'size_id', 'size_name', 'discount_percent', 'discounted_price', 
        'regular_price', 'product_attributes_values', 'thumbnail_url']
