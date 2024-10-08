import torch
from torchvision.transforms.functional import to_pil_image
import matplotlib.pyplot as plt

from Generator import Generator
from Discriminator import Discriminator


class CycleGANTrainer:
	def __init__(self, gen_A2B: Generator, gen_B2A: Generator,
			disc_A: Discriminator, disc_B: Discriminator,
			optimizer_G, optimizer_D_A, optimizer_D_B, criterion_GAN, criterion_cycle,
			save_path: str
		):
		self.gen_A2B = gen_A2B
		self.gen_B2A = gen_B2A
		self.disc_A = disc_A
		self.disc_B = disc_B
		self.optimizer_G = optimizer_G
		self.optimizer_D_A = optimizer_D_A
		self.optimizer_D_B = optimizer_D_B
		self.criterion_GAN = criterion_GAN
		self.criterion_cycle = criterion_cycle
		self.save_path = save_path

	def train_step(self, real_A, real_B):
		lambda_cycle = 10
		# Переместите данные на устройство (GPU, если доступен)
		real_A, real_B = real_A.to(device), real_B.to(device)

		# Обучение генератора
		self.optimizer_G.zero_grad()

		fake_B = self.gen_A2B(real_A)
		rec_A = self.gen_B2A(fake_B)

		fake_A = self.gen_B2A(real_B)
		rec_B = self.gen_A2B(fake_A)

		# Adversarial loss
		loss_GAN_A2B = self.criterion_GAN(self.disc_B(fake_B), torch.ones_like(self.disc_B(fake_B)))
		loss_GAN_B2A = self.criterion_GAN(self.disc_A(fake_A), torch.ones_like(self.disc_A(fake_A)))

		# Cycle-consistency loss
		loss_cycle_A = self.criterion_cycle(rec_A, real_A)
		loss_cycle_B = self.criterion_cycle(rec_B, real_B)

		# Total generator loss
		loss_G = loss_GAN_A2B + loss_GAN_B2A + lambda_cycle * (loss_cycle_A + loss_cycle_B)

		loss_G.backward()
		self.optimizer_G.step()

		# Обучение дискриминатора A
		self.optimizer_D_A.zero_grad()

		loss_D_A_real = self.criterion_GAN(self.disc_A(real_A), torch.ones_like(self.disc_A(real_A)))
		loss_D_A_fake = self.criterion_GAN(self.disc_A(fake_A.detach()), torch.zeros_like(self.disc_A(fake_A.detach())))

		loss_D_A = 0.5 * (loss_D_A_real + loss_D_A_fake)

		loss_D_A.backward()
		self.optimizer_D_A.step()

		# Обучение дискриминатора B
		self.optimizer_D_B.zero_grad()

		loss_D_B_real = self.criterion_GAN(self.disc_B(real_B), torch.ones_like(self.disc_B(real_B)))
		loss_D_B_fake = self.criterion_GAN(self.disc_B(fake_B.detach()), torch.zeros_like(self.disc_B(fake_B.detach())))

		loss_D_B = 0.5 * (loss_D_B_real + loss_D_B_fake)

		loss_D_B.backward()
		self.optimizer_D_B.step()

	def visualize_results(self, real_A, real_B):
		# Перевести модели в режим оценки (eval mode)
		self.gen_A2B.eval()
		self.gen_B2A.eval()

		# Сгенерировать изображения
		fake_B = self.gen_A2B(real_A)
		fake_A = self.gen_B2A(real_B)

		# Перевести обратно в режим обучения (train mode)
		self.gen_A2B.train()
		self.gen_B2A.train()

		# Преобразовать тензоры в изображенияч
		real_A_img = to_pil_image(real_A[0].cpu())
		real_B_img = to_pil_image(real_B[0].cpu())
		fake_A_img = to_pil_image(fake_A[0].cpu())
		fake_B_img = to_pil_image(fake_B[0].cpu())

		# Отобразить изображения
		fig, axes = plt.subplots(2, 2, figsize=(8, 8))

		axes[0, 0].imshow(real_A_img)
		axes[0, 0].set_title('Real A')
		axes[0, 0].axis('off')

		axes[0, 1].imshow(fake_B_img)
		axes[0, 1].set_title('Generated B')
		axes[0, 1].axis('off')

		axes[1, 0].imshow(real_B_img)
		axes[1, 0].set_title('Real B')
		axes[1, 0].axis('off')

		axes[1, 1].imshow(fake_A_img)
		axes[1, 1].set_title('Generated A')
		axes[1, 1].axis('off')

		plt.show()

	def save_models(self):
		torch.save(self.gen_A2B.state_dict(), self.save_path + 'gen_A2B.pth')
		torch.save(self.gen_B2A.state_dict(), self.save_path + 'gen_B2A.pth')
		torch.save(self.disc_A.state_dict(), self.save_path + 'disc_A.pth')
		torch.save(self.disc_B.state_dict(), self.save_path + 'disc_B.pth')

		torch.save(self.optimizer_G.state_dict(), self.save_path + 'optimizer_G.pth')
		torch.save(self.optimizer_D_A.state_dict(), self.save_path + 'optimizer_D_A.pth')
		torch.save(self.optimizer_D_B.state_dict(), self.save_path + 'optimizer_D_B.pth')

