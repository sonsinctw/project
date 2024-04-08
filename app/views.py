# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from PIL import Image
from pyzbar.pyzbar import decode
import requests
from .models import Product, HistoryEntry
from .forms import ProductForm
from django.http import HttpResponseRedirect

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index')
        else:
            return render(request, 'app/login.html', {'error_message': 'Invalid login'})
    else:
        return render(request, 'app/login.html')

@login_required
def logout(request):
    auth_logout(request)
    return redirect('login')

@login_required
def read_barcode_view(request):
    if request.method == 'POST' and 'image' in request.FILES:
        image = Image.open(request.FILES['image'])
        decoded_objects = decode(image)
        if decoded_objects:
            barcode_data = decoded_objects[0].data.decode('utf-8')
            product = Product.objects.filter(product_code=barcode_data).first()
            if product:
                return JsonResponse({'success': True, 'product_id': product.id})
            else:
                return JsonResponse({'success': False, 'message': 'Product not found.'})
        else:
            return JsonResponse({'success': False, 'message': 'No barcode detected.'})
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request.'})

@login_required
def product_detail_view(request, id):
    product = Product.objects.get(pk=id)
    # ส่งสถานะการเชื่อมต่อไปยัง template
    return render(request, 'app/product_detail.html', {'product': product})

@login_required
def index_view(request):
    filter_by = request.GET.get('filter')
    search_query = request.GET.get('search_query')

    products = Product.objects.all()

    if filter_by == 'available':
        products = products.filter(status=True)
    elif filter_by == 'out_of_stock':
        products = products.filter(status=False)

    if search_query:
        products = products.filter(
            Q(product_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(shelf__icontains=search_query)
        )

    history = HistoryEntry.objects.all()

    return render(request, 'app/index.html', {'products': products, 'history': history})

@login_required
def view_product_view(request, id):
    product = get_object_or_404(Product, pk=id)
    return render(request, 'app/view_product.html', {'product': product})

@login_required
def add_product_view(request):
    if request.method == 'GET':
        used_shelves = Product.objects.values_list('shelf', flat=True).distinct()
        all_shelves = [choice[0] for choice in Product.SHELF_CHOICES]
        available_shelves = [shelf for shelf in all_shelves if shelf not in used_shelves]
        form = ProductForm(shelf_choices=available_shelves)
        return render(request, 'app/add.html', {'form': form})
    elif request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            HistoryEntry.objects.create(action='add', product_code=product.product_code)
            return redirect('index')
        return render(request, 'app/add.html', {'form': form})

@login_required
def edit_product_view(request, id):
    product = get_object_or_404(Product, pk=id)
    if request.method == 'GET':
        form = ProductForm(instance=product)
        del form.fields['shelf']
        return render(request, 'app/edit.html', {'form': form})
    elif request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()  
            HistoryEntry.objects.create(action='edit', product_code=product.product_code)
            return redirect(reverse('product_detail', kwargs={'id': id}))
        return render(request, 'app/edit.html', {'form': form})

@login_required
def delete_product_view(request, id):
    product = get_object_or_404(Product, pk=id)
    if request.method == 'GET':
        return render(request, 'app/delete.html', {'product': product})
    elif request.method == 'POST':
        product.delete()
        HistoryEntry.objects.create(action='delete', product_code=product.product_code)
        return redirect('index')

@login_required
def history_view(request):
    history_entries = HistoryEntry.objects.all()
    return render(request, 'app/history.html', {'history': history_entries})

@login_required
def clear_history_view(request):
    if request.method == 'POST':
        HistoryEntry.objects.all().delete()
        return redirect('history')

@login_required
def move_product_view(request, id):
    product = get_object_or_404(Product, pk=id)
    if request.method == 'GET':
        current_shelf = product.shelf
        used_shelves = Product.objects.exclude(pk=id).values_list('shelf', flat=True).distinct()
        all_shelves = [choice[0] for choice in Product.SHELF_CHOICES]
        available_shelves = [shelf for shelf in all_shelves if shelf not in used_shelves]
        return render(request, 'app/move_product.html', {'product': product, 'available_shelves': available_shelves})
    elif request.method == 'POST':
        current_shelf = product.shelf
        new_shelf = request.POST.get('new_shelf')
        product.shelf = new_shelf
        product.save()
        command = f"MoveFrom{current_shelf}To{new_shelf}"
        send_command_to_nodeMCU(command)
        HistoryEntry.objects.create(action='move', product_code=product.product_code)
        return redirect('product_detail', id=id)

@csrf_exempt
def update_shelf_view(request, id):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=id)
        current_shelf = product.shelf
        new_shelf = request.POST.get('new_shelf')
        command = f"MoveFrom{current_shelf}To{new_shelf}"
        response = send_command_to_nodeMCU(request, command)  # เรียกใช้ฟังก์ชัน send_command_to_nodeMCU
        if response.get('success', True):
            product.shelf = new_shelf
            product.save()
            HistoryEntry.objects.create(action='move', product_code=product.product_code)
            return HttpResponseRedirect(reverse('product_detail', args=[id]))  # โหลดหน้า product_detail อีกครั้งหลังจากการอัพเดท
        else:
            # หากเกิดข้อผิดพลาด โหลดหน้า product_detail อีกครั้ง
            return HttpResponseRedirect(reverse('product_detail', args=[id]))

# ในฟังก์ชัน update_status_view
@csrf_exempt
def update_status_view(request, id):
    if request.method == 'POST':
        product = Product.objects.get(pk=id)
        product.status = not product.status
        action = 'picking' if product.status else 'put away'
        command = f"PutAway{product.shelf}" if product.status else f"Picking{product.shelf}"
        response = send_command_to_nodeMCU(request, command)  # เรียกใช้ฟังก์ชัน send_command_to_nodeMCU
        if response.get('success', True):
            product.save()
            HistoryEntry.objects.create(action=action, product_code=product.product_code)
            return HttpResponseRedirect(reverse('index'))  # โหลดหน้า index อีกครั้งหลังจากการอัพเดท
        else:
            # หากเกิดข้อผิดพลาด โหลดหน้า index อีกครั้ง
            return HttpResponseRedirect(reverse('index'))


# url = "http://192.168.1.162/command_endpoint"

def send_command_to_nodeMCU(request, command):
    try:
        # รับ URL ของ NodeMCU จาก session
        url = request.session.get('nodeMCU_url')
        if url:
            # ส่งคำสั่งไปยัง NodeMCU ด้วยการ POST และรอคำตอบ
            response = requests.post(url, data={'command': command})
            if response.status_code == 200:
                # ตรวจสอบคำตอบที่ได้รับจาก NodeMCU
                if response.text.strip() == "Success":
                    print("Command sent successfully to ESP8266")
                    return JsonResponse({'success': True})
                else:
                    print("Failed to execute command on ESP8266")
                    return JsonResponse({'success': False, 'message': 'Failed to execute command on ESP8266'})
            else:
                print("Failed to send command to ESP8266")
                return JsonResponse({'success': False, 'message': 'Failed to send command to ESP8266'})
        else:
            print("NodeMCU URL is not set.")
            return JsonResponse({'success': False, 'message': 'NodeMCU URL is not set.'})
    except requests.exceptions.RequestException as e:
        print("Connection to server failed:", e)
        return JsonResponse({'success': False, 'message': 'Connection to server failed'})

# เพิ่มเติมฟังก์ชัน check_connection_view
def check_connection_view(request):
    try:
        url = request.session.get('nodeMCU_url')
        if url:
            response = requests.post(url, data={'command': 'CheckConnection'})
            if response.status_code == 200:
                nodemcu_connected = True
                return JsonResponse({'nodemcu_connected': nodemcu_connected})
            else:
                nodemcu_connected = False
                return JsonResponse({'nodemcu_connected': nodemcu_connected})
        else:
            nodemcu_connected = False
            return JsonResponse({'nodemcu_connected': nodemcu_connected})
    except requests.exceptions.RequestException:
        nodemcu_connected = False
        return JsonResponse({'nodemcu_connected': nodemcu_connected})

@login_required
def change_ip_view(request):
    if request.method == 'POST':
        new_ip = request.POST.get('ipAddress')
        if new_ip:
            # สร้างตัวแปร url จาก new_ip
            url = f"http://{new_ip}/command_endpoint"
            # บันทึก url ใน session
            request.session['nodeMCU_url'] = url
            return HttpResponseRedirect(reverse('index'))
    return render(request, 'app/change_ip.html')


