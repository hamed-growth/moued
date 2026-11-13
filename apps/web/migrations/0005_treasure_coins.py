from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('missions', '0004_missioncategory_mission_coins_mission_description_and_more')]

    operations = [
        migrations.AddField(
            model_name='treasurepurchase', name='currency',
            field=models.CharField(max_length=6, default='points', verbose_name='ارز خرید', choices=[
                ('points', 'امتیاز'), ('coins', 'سکه'),
            ]),
        ),
        migrations.AlterField(
            model_name='treasureitem', name='price',
            field=models.PositiveIntegerField(default=100, verbose_name='قیمت (سکه)', help_text='سکه لازم برای خرید این آیتم.'),
        ),
        migrations.AlterField(
            model_name='treasurepurchase', name='status',
            field=models.CharField(max_length=15, default='pending', verbose_name='وضعیت', choices=[
                ('pending', 'در انتظار تأیید'), ('delivered', 'تأیید شده'), ('cancelled', 'رد شده'),
            ]),
        ),
    ]
